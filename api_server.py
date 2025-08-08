"""
Trading Bot Web API Backend
==========================

FastAPI backend for the crypto trading bot with Coinbase Pro integration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
import uvicorn
import secrets
import time
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Import our trading bot components
from utils.exchange_handler import ExchangeHandler
from utils.portfolio_manager import PortfolioManager
from utils.risk_manager import RiskManager
from utils.multi_strategy_trader import MultiStrategyTrader
from utils.gpu_acceleration import gpu_accelerator
from utils.demo_data import demo_service
from utils.websocket_manager import ConnectionManager
from utils.rate_limiter import RateLimiter

# Initialize WebSocket manager
manager = ConnectionManager()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradingBotAPI")

# Initialize FastAPI app
app = FastAPI(
    title="GPU-Accelerated Crypto Trading Bot",
    description="Web interface for managing your crypto trading bot",
    version="1.0.0"
)

# Enable CORS for frontend with improved security
# Use environment variable to control allowed origins
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
logger.info(f"Configuring CORS with allowed origins: {allowed_origins}")

# Add CORS middleware with proper security settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "X-API-Key"],
    expose_headers=["Content-Disposition"],
    max_age=600  # Cache preflight requests for 10 minutes
)

# Enable gzip compression for faster transfers
app.add_middleware(GZipMiddleware, minimum_size=500)

# Add simple cache-control based on path
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path.endswith(".html") or path == "/":
            response.headers["Cache-Control"] = "no-cache"
        return response

app.add_middleware(CacheControlMiddleware)

# Add rate limiting for production (adjust parameters as needed)
# Disable in development by setting ENABLE_RATE_LIMIT=0
if os.environ.get("ENABLE_RATE_LIMIT", "1") == "1":
    # Configure rate limits
    max_requests = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "100"))
    window_seconds = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
    block_time = int(os.environ.get("RATE_LIMIT_BLOCK_TIME", "300"))
    
    # Add rate limiter middleware
    app.add_middleware(
        RateLimiter,
        max_requests=max_requests,
        window_seconds=window_seconds,
        block_time_seconds=block_time
    )
    logger.info(f"Rate limiting enabled: {max_requests} requests per {window_seconds}s")
else:
    logger.info("Rate limiting disabled (development mode)")

# Global trading bot instance
trading_bot = None
demo_mode = False
bot_status = {
    "running": False,
    "connected": False,
    "demo_mode": False,
    "last_update": None,
    "error": None
}

# Pydantic models for API requests/responses
class LoginRequest(BaseModel):
    api_key: str
    api_secret: str
    api_passphrase: str
    sandbox: bool = True

class TradingConfig(BaseModel):
    total_budget: float = 50.0
    max_trades: int = 10
    stop_loss: float = 3.0
    take_profit: float = 8.0
    strategies: List[str] = ["gpu_rsi_strategy", "gpu_volatility_breakout", "gpu_moving_average_cross"]

class TradeOrder(BaseModel):
    symbol: str
    side: str  # "buy" or "sell"
    amount: float
    strategy: str

# API Routes

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main UI"""
    return FileResponse("frontend/index.html")

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Authenticate with Coinbase Pro"""
    global trading_bot, bot_status, demo_mode
    
    # Check for demo mode (empty credentials)
    if not request.api_key or not request.api_secret or not request.api_passphrase:
        demo_mode = True
        bot_status.update({
            "connected": True,
            "demo_mode": True,
            "last_update": datetime.now().isoformat(),
            "error": None
        })
        
        return {
            "success": True,
            "message": "Connected in DEMO mode - No real trading will occur",
            "demo_mode": True,
            "gpu_status": {
                "gpu_available": gpu_accelerator.gpu_available,
                "use_opencl": gpu_accelerator.use_opencl,
                "use_rocm": gpu_accelerator.use_rocm,
                "use_numba": gpu_accelerator.use_numba,
                "use_polars": gpu_accelerator.use_polars,
                "acceleration_type": "AMD-optimized" if gpu_accelerator.gpu_available else "CPU-only"
            }
        }
    
    try:
        # Initialize exchange handler with multiple fallback options
        exchange_options = [
            ("coinbase", "Coinbase Pro"),
            ("coinbasepro", "Coinbase Pro (Legacy)"), 
            ("binance", "Binance (Fallback)"),
            ("kraken", "Kraken (Fallback)")
        ]
        
        exchange_handler = None
        connection_error = None
        
        for exchange_id, exchange_name in exchange_options:
            try:
                exchange_handler = ExchangeHandler(
                    exchange_id, 
                    request.api_key, 
                    request.api_secret,
                    sandbox=request.sandbox,
                    passphrase=request.api_passphrase
                )
                
                # Test connection
                await asyncio.to_thread(exchange_handler.get_balance)
                logger.info(f"Successfully connected to {exchange_name}")
                break
                
            except Exception as e:
                logger.warning(f"Failed to connect to {exchange_name}: {str(e)}")
                connection_error = str(e)
                continue
        
        if not exchange_handler:
            raise Exception(f"Could not connect to any supported exchange. Last error: {connection_error}")
        
        # Initialize trading components
        portfolio_manager = PortfolioManager(exchange_handler, total_budget=50.0)
        risk_manager = RiskManager(exchange_handler, portfolio_manager)
        
        # Initialize multi-strategy trader with GPU acceleration
        trading_bot = MultiStrategyTrader(exchange_handler, portfolio_manager, risk_manager)
        trading_bot.initialize_gpu_strategies()
        
        demo_mode = False
        bot_status.update({
            "connected": True,
            "demo_mode": False,
            "last_update": datetime.now().isoformat(),
            "error": None
        })
        
        return {
            "success": True,
            "message": f"Successfully connected to {exchange_handler.exchange_id}",
            "exchange": exchange_handler.exchange_id,
            "demo_mode": False,
            "gpu_status": {
                "gpu_available": gpu_accelerator.gpu_available,
                "use_opencl": gpu_accelerator.use_opencl,
                "use_rocm": gpu_accelerator.use_rocm,
                "use_numba": gpu_accelerator.use_numba,
                "use_polars": gpu_accelerator.use_polars,
                "acceleration_type": "AMD-optimized" if gpu_accelerator.gpu_available else "CPU-only"
            }
        }
        
    except Exception as e:
        bot_status.update({
            "connected": False,
            "demo_mode": False,
            "error": str(e),
            "last_update": datetime.now().isoformat()
        })
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/status")
async def get_status():
    """Get trading bot status"""
    global demo_mode, bot_status, trading_bot
    
    try:
        # Basic status
        status = {
            "connected": bot_status.get("connected", False),
            "running": bot_status.get("running", False),
            "demo_mode": demo_mode,
            "last_update": bot_status.get("last_update"),
            "error": bot_status.get("error"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add real exchange info if connected
        if not demo_mode and trading_bot:
            try:
                # Get real account info
                balance = await asyncio.to_thread(trading_bot.exchange_handler.get_balance)
                
                # Calculate total portfolio value in USD
                total_usd = 0
                if 'USD' in balance:
                    total_usd += balance['USD'].get('total', 0)
                
                # Add crypto values (simplified - you could add real-time conversion)
                for symbol, bal in balance.items():
                    if symbol != 'USD' and bal.get('total', 0) > 0:
                        try:
                            ticker = await asyncio.to_thread(
                                trading_bot.exchange_handler.exchange.fetch_ticker, 
                                f"{symbol}/USD"
                            )
                            total_usd += bal.get('total', 0) * ticker.get('last', 0)
                        except Exception:
                            pass  # Skip if can't get price
                
                status.update({
                    "exchange": trading_bot.exchange_handler.exchange_id,
                    "portfolio_value_usd": round(total_usd, 2),
                    "balances": {k: v for k, v in balance.items() if v.get('total', 0) > 0.001},
                    "strategies_active": len(trading_bot.strategies) if trading_bot.strategies else 0
                })
                
            except Exception as e:
                logger.warning(f"Could not get real exchange status: {e}")
                status["exchange_error"] = str(e)
        
        # Add demo status if in demo mode
        if demo_mode:
            status.update({
                "portfolio": demo_service.get_demo_portfolio_status(),
                "gpu_status": demo_service.get_demo_gpu_status()
            })
        
        return status
        
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return {
            "connected": False,
            "running": False,
            "demo_mode": demo_mode,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/trading/start")
async def start_trading(background_tasks: BackgroundTasks):
    """Start automated trading"""
    global bot_status
    
    if demo_mode:
        bot_status["running"] = True
        bot_status["last_update"] = datetime.now().isoformat()
        return {"success": True, "message": "Demo trading started (simulation mode)"}
    
    if not trading_bot:
        raise HTTPException(status_code=400, detail="Not connected to exchange")
    
    if bot_status["running"]:
        return {"success": True, "message": "Trading already running"}
    
    try:
        # Initialize strategies if not already done
        if not trading_bot.strategies:
            logger.info("Initializing GPU strategies...")
            trading_bot.initialize_gpu_strategies()
            logger.info("GPU strategies initialized")
        
        # Start trading in background - make it truly async
        background_tasks.add_task(run_trading_bot)
        bot_status["running"] = True
        bot_status["last_update"] = datetime.now().isoformat()
        bot_status["error"] = None
        
        logger.info("Trading started successfully")
        return {"success": True, "message": "Real trading started with live Coinbase data"}
        
    except Exception as e:
        logger.error(f"Failed to start trading: {e}")
        bot_status["error"] = str(e)
        bot_status["running"] = False
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trading/stop")
async def stop_trading():
    """Stop automated trading"""
    global bot_status
    
    if demo_mode:
        bot_status["running"] = False
        bot_status["last_update"] = datetime.now().isoformat()
        return {"success": True, "message": "Demo trading stopped"}
    
    if not trading_bot:
        raise HTTPException(status_code=400, detail="Not connected to exchange")
    
    try:
        if bot_status["running"]:
            trading_bot.stop_trading()
            bot_status["running"] = False
            bot_status["last_update"] = datetime.now().isoformat()
        
        return {"success": True, "message": "Trading stopped"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio")
async def get_portfolio():
    """Get portfolio information"""
    if demo_mode:
        return {
            "portfolio": demo_service.get_demo_portfolio_status(),
            "balance": demo_service.get_demo_balance(),
            "timestamp": datetime.now().isoformat()
        }
    
    if not trading_bot:
        raise HTTPException(status_code=400, detail="Not connected to exchange")
    
    try:
        # Get real portfolio data from exchange
        portfolio_status = trading_bot.portfolio_manager.get_portfolio_status()
        
        # Get real balance from exchange with proper error handling
        try:
            balance = await asyncio.to_thread(trading_bot.exchange_handler.get_balance)
        except Exception as balance_error:
            logger.error(f"Failed to get balance: {balance_error}")
            # Provide fallback data structure
            balance = {
                "USD": {"free": 0.0, "used": 0.0, "total": 0.0},
                "BTC": {"free": 0.0, "used": 0.0, "total": 0.0},
                "ETH": {"free": 0.0, "used": 0.0, "total": 0.0}
            }
        
        return {
            "portfolio": portfolio_status,
            "balance": balance,
            "demo_mode": False,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Portfolio endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategies")
async def get_strategies():
    """Get strategy performance and configuration"""
    if demo_mode:
        return demo_service.get_demo_strategies()
    
    if not trading_bot:
        raise HTTPException(status_code=400, detail="Not connected to exchange")
    
    try:
        strategies_info = {}
        
        for strategy_name, strategy_info in trading_bot.strategies.items():
            # Get performance metrics if available
            performance_metrics = {}
            if hasattr(strategy_info["instance"], "get_performance_metrics"):
                performance_metrics = strategy_info["instance"].get_performance_metrics()
            
            strategies_info[strategy_name] = {
                "symbols": strategy_info.get("symbols", []),
                "trade_count": strategy_info.get("trade_count", 0),
                "successful_trades": strategy_info.get("successful_trades", 0),
                "failed_trades": strategy_info.get("failed_trades", 0),
                "last_execution": strategy_info.get("last_execution", {}),
                "performance_metrics": performance_metrics
            }
        
        return strategies_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategies/benchmark")
async def benchmark_strategies():
    """Run GPU vs CPU performance benchmark"""
    if demo_mode:
        return {
            "benchmark_results": demo_service.get_demo_benchmark_results(),
            "timestamp": datetime.now().isoformat()
        }
    
    if not trading_bot:
        raise HTTPException(status_code=400, detail="Not connected to exchange")
    
    try:
        benchmark_results = trading_bot.benchmark_gpu_performance()
        return {
            "benchmark_results": benchmark_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/{symbol}")
async def get_market_data(symbol: str):
    """Get market data for a symbol"""
    if demo_mode:
        ticker = demo_service.get_demo_ticker(symbol)
        if not ticker:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        return {
            "symbol": symbol,
            "price": ticker["last"],
            "bid": ticker["bid"],
            "ask": ticker["ask"],
            "volume": ticker["quoteVolume"],
            "change": ticker["percentage"],
            "timestamp": datetime.now().isoformat()
        }
    
    if not trading_bot:
        raise HTTPException(status_code=400, detail="Not connected to exchange")
    
    try:
        ticker = await asyncio.to_thread(
            trading_bot.exchange_handler.exchange.fetch_ticker, 
            symbol
        )
        
        return {
            "symbol": symbol,
            "price": ticker["last"],
            "bid": ticker["bid"],
            "ask": ticker["ask"],
            "volume": ticker["quoteVolume"],
            "change": ticker["percentage"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trade/manual")
async def manual_trade(order: TradeOrder):
    """Execute a manual trade"""
    if demo_mode:
        try:
            result = demo_service.place_demo_order(order.symbol, order.side, order.amount)
            return {
                "success": True,
                "order_id": result["id"],
                "symbol": order.symbol,
                "side": order.side,
                "amount": order.amount,
                "demo_mode": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    if not trading_bot:
        raise HTTPException(status_code=400, detail="Not connected to exchange")
    
    try:
        # Check if we can make this trade
        portfolio_status = trading_bot.portfolio_manager.get_portfolio_status()
        
        if portfolio_status["available_budget"] < order.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")
        
        # Execute trade through exchange handler
        result = await asyncio.to_thread(
            trading_bot.exchange_handler.place_order,
            order.symbol,
            order.side,
            order.amount
        )
        
        return {
            "success": True,
            "order_id": result.get("id"),
            "symbol": order.symbol,
            "side": order.side,
            "amount": order.amount,
            "demo_mode": False,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades/history")
async def get_trade_history():
    """Get trade history"""
    if demo_mode:
        return {
            "trades": demo_service.get_demo_trade_history(),
            "timestamp": datetime.now().isoformat()
        }
    
    if not trading_bot:
        raise HTTPException(status_code=400, detail="Not connected to exchange")
    
    try:
        # Get recent trades from exchange
        trades = await asyncio.to_thread(
            trading_bot.exchange_handler.get_trade_history,
            limit=50
        )
        
        return {
            "trades": trades,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_logs():
    """Get recent log entries"""
    if demo_mode:
        return {
            "logs": demo_service.get_demo_logs(),
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        log_file = "logs/trading_bot.log"
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                lines = f.readlines()
                # Return last 100 lines
                recent_logs = lines[-100:] if len(lines) > 100 else lines
                
            return {
                "logs": recent_logs,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"logs": [], "message": "No log file found"}
            
    except Exception as e:
        return {"logs": [], "error": str(e)}

@app.get("/api/auth/demo")
@app.post("/api/auth/demo")
async def demo_login():
    """Enter demo mode without real credentials"""
    global demo_mode, bot_status
    
    demo_mode = True
    bot_status.update({
        "connected": True,
        "demo_mode": True,
        "running": False,
        "last_update": datetime.now().isoformat(),
        "error": None
    })
    
    return {
        "success": True,
        "message": "Entered DEMO mode - No real trading will occur",
        "demo_mode": True,
        "gpu_status": demo_service.get_demo_gpu_status()
    }

@app.get("/api/test-connection")
async def test_connection():
    """Test the current exchange connection"""
    if demo_mode:
        return {
            "success": True,
            "message": "Demo mode - connection simulated",
            "demo_mode": True
        }
    
    if not trading_bot:
        raise HTTPException(status_code=400, detail="Not connected to exchange")
    
    try:
        # Test basic exchange connectivity
        balance = await asyncio.to_thread(trading_bot.exchange_handler.get_balance)
        
        # Test market data access
        ticker = await asyncio.to_thread(
            trading_bot.exchange_handler.exchange.fetch_ticker, 
            'BTC/USD'
        )
        
        return {
            "success": True,
            "message": f"Successfully connected to {trading_bot.exchange_handler.exchange_id}",
            "exchange": trading_bot.exchange_handler.exchange_id,
            "account_currencies": list(balance.keys()),
            "btc_price": ticker.get('last', 'N/A'),
            "demo_mode": False
        }
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    # Get query parameters for basic auth
    token = websocket.query_params.get("token")
    session_id = websocket.query_params.get("session_id")
    
    # Validate connection - in production, use a proper token validation system
    # For now, accept all connections in demo mode or with any token
    is_valid = demo_mode or token is not None
    
    if not is_valid:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    # Accept the connection
    await manager.connect(websocket)
    client_id = session_id or str(id(websocket))
    logger.info(f"WebSocket client connected: {client_id}")
    
    try:
        # Send initial status upon connection
        await send_immediate_update(websocket)
        
        # Process messages
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get('type') == 'ping':
                    await websocket.send_text(json.dumps({'type': 'pong', 'timestamp': datetime.now().isoformat()}))
                elif message.get('type') == 'request_update':
                    # Client requesting immediate update
                    await send_immediate_update(websocket)
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({'type': 'error', 'message': 'Invalid JSON'}))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def send_immediate_update(websocket: WebSocket):
    """Send immediate update to a specific websocket"""
    try:
        if demo_mode:
            data = {
                'type': 'immediate_update',
                'data': {
                    'portfolio': demo_service.get_demo_portfolio_status(),
                    'strategies': demo_service.get_demo_strategies(),
                    'gpu_status': demo_service.get_demo_gpu_status(),
                    'bot_status': bot_status
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            if trading_bot:
                data = {
                    'type': 'immediate_update',
                    'data': {
                        'portfolio': trading_bot.portfolio_manager.get_portfolio_status(),
                        'strategies': {
                            name: {
                                "total_trades": info.get("trade_count", 0),
                                "successful_trades": info.get("successful_trades", 0),
                                "symbols": info.get("symbols", [])
                            }
                            for name, info in trading_bot.strategies.items()
                        },
                        'gpu_status': {
                            "gpu_available": gpu_accelerator.gpu_available,
                            "use_opencl": gpu_accelerator.use_opencl,
                            "use_rocm": gpu_accelerator.use_rocm,
                            "use_numba": gpu_accelerator.use_numba,
                            "use_polars": gpu_accelerator.use_polars,
                            "acceleration_type": "AMD-optimized" if gpu_accelerator.gpu_available else "CPU-only"
                        },
                        'bot_status': bot_status
                    },
                    'timestamp': datetime.now().isoformat()
                }
            else:
                data = {
                    'type': 'immediate_update',
                    'data': {'error': 'Not connected'},
                    'timestamp': datetime.now().isoformat()
                }
        
        await manager.send_personal_message(json.dumps(data), websocket)
        
    except Exception as e:
        logger.error(f"Error sending immediate update: {e}")

@app.get("/api/realtime/status")
async def get_realtime_status():
    """Get real-time WebSocket connection status"""
    return {
        "connections": len(manager.active_connections),
        "updates_active": manager.is_running,
        "timestamp": datetime.now().isoformat()
    }

# Background task to run the trading bot
async def run_trading_bot():
    """Background task to run the trading bot"""
    global bot_status
    
    try:
        logger.info("Starting trading bot background task...")
        
        # Make sure trading bot is properly initialized
        if not trading_bot:
            raise Exception("Trading bot not initialized")
        
        # Start the trading bot in a separate thread to avoid blocking
        def start_bot_thread():
            try:
                trading_bot.start_trading()
                logger.info("Trading bot started successfully")
            except Exception as e:
                logger.error(f"Error in trading bot thread: {e}")
                bot_status["error"] = str(e)
                bot_status["running"] = False
        
        import threading
        bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
        bot_thread.start()
        
        # Monitor the bot status
        while bot_status["running"]:
            await asyncio.sleep(10)  # Check every 10 seconds
            bot_status["last_update"] = datetime.now().isoformat()
            
            # Check if bot is still alive by testing exchange connection
            try:
                if trading_bot and trading_bot.exchange_handler:
                    # Quick health check
                    await asyncio.to_thread(trading_bot.exchange_handler.exchange.fetch_ticker, 'BTC/USD')
            except Exception as health_error:
                logger.warning(f"Bot health check failed: {health_error}")
        
        logger.info("Trading bot background task stopped")
            
    except Exception as e:
        logger.error(f"Trading bot background task error: {e}")
        bot_status["error"] = str(e)
        bot_status["running"] = False

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

if __name__ == "__main__":
    import uvicorn
    import asyncio
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    async def startup():
        # Start WebSocket manager background tasks
        asyncio.create_task(manager.start_real_time_updates())
    
    # Add startup event to FastAPI
    @app.on_event("startup")
    async def on_startup():
        await startup()
    
    # Run the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        reload=False  # Disable reload for proper WebSocket handling
    )

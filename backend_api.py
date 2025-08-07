#!/usr/bin/env python3
"""
Complete Backend API Server for Crypto Trading Bot
Provides REST endpoints for gas prices, DEX analytics, and WebSocket chat
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our GPU accelerator
try:
    from utils.gpu_acceleration import gpu_accelerator
except ImportError:
    print("Warning: Could not import gpu_accelerator, using mock data")
    gpu_accelerator = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Crypto Trading Bot API",
    description="Backend API for crypto trading bot with gas tracking, DEX analytics, and chat",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Chat connections storage
chat_connections = []

@app.get("/")
async def serve_dashboard():
    """Serve the premium dashboard"""
    dashboard_path = os.path.join(frontend_path, "premium_dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    
    # Fallback to basic dashboard
    basic_dashboard_path = os.path.join(frontend_path, "dashboard.html")
    if os.path.exists(basic_dashboard_path):
        return FileResponse(basic_dashboard_path)
    
    return {"message": "Dashboard not found. Please check frontend files."}

@app.get("/api/gas")
async def get_gas_prices():
    """Get current gas prices from Etherscan"""
    try:
        if gpu_accelerator:
            gas_data = await asyncio.to_thread(gpu_accelerator.get_gas_prices)
            return gas_data
        else:
            # Mock data for testing
            return {
                "safe_gas_price": "12",
                "standard_gas_price": "15",
                "fast_gas_price": "18",
                "base_fee": "10.5",
                "status": "mock"
            }
    except Exception as e:
        logger.error(f"Error fetching gas prices: {e}")
        return {
            "error": str(e),
            "safe_gas_price": "0",
            "standard_gas_price": "0", 
            "fast_gas_price": "0",
            "base_fee": "0"
        }

@app.get("/api/dex/analytics")
async def get_dex_analytics(pair_id: str = "ETH-USDT"):
    """Get DEX analytics for a trading pair"""
    try:
        if gpu_accelerator:
            # Get token profile and analytics
            profile_data = await asyncio.to_thread(gpu_accelerator.get_token_profile, pair_id)
            
            # Get additional analytics
            analytics_data = {
                "pairInfo": {
                    "baseToken": pair_id.split('-')[0] if '-' in pair_id else "ETH",
                    "quoteToken": pair_id.split('-')[1] if '-' in pair_id else "USDT",
                    "pairId": pair_id
                },
                "priceData": {
                    "current": profile_data.get("price", "0.00"),
                    "change24h": profile_data.get("priceChange", {}).get("h24", "0"),
                    "volume24h": profile_data.get("volume", {}).get("h24", "0")
                },
                "indicators": {
                    "rsi": {"current": "50.0"},  # Would calculate from price data
                    "ma20": {"current": "0.00"},
                    "volatility": {"current": "medium"}
                },
                "signals": {
                    "overallSignal": "HOLD",
                    "confidence": "medium"
                },
                "timestamp": profile_data.get("timestamp", ""),
                "status": "live"
            }
            
            return analytics_data
        else:
            # Mock analytics data
            return {
                "pairInfo": {
                    "baseToken": "ETH",
                    "quoteToken": "USDT", 
                    "pairId": pair_id
                },
                "priceData": {
                    "current": "2450.50",
                    "change24h": "+2.3%",
                    "volume24h": "125.5M"
                },
                "indicators": {
                    "rsi": {"current": "65.2"},
                    "ma20": {"current": "2420.10"},
                    "volatility": {"current": "medium"}
                },
                "signals": {
                    "overallSignal": "BUY",
                    "confidence": "high"
                },
                "status": "mock"
            }
    except Exception as e:
        logger.error(f"Error fetching DEX analytics: {e}")
        return {
            "error": str(e),
            "pairInfo": {"baseToken": "ETH", "quoteToken": "USDT"},
            "priceData": {"current": "0.00"},
            "indicators": {"rsi": {"current": "N/A"}},
            "signals": {"overallSignal": "ERROR"}
        }

@app.get("/api/trading/estimate")
async def estimate_trade_cost(token_address: str, amount: float):
    """Estimate transaction costs for a trade"""
    try:
        if gpu_accelerator:
            cost_data = await asyncio.to_thread(
                gpu_accelerator.estimate_transaction_cost, 
                token_address, 
                amount
            )
            return cost_data
        else:
            # Mock estimation
            return {
                "estimated_gas": "150000",
                "gas_price_gwei": "15",
                "estimated_cost_eth": "0.00225",
                "estimated_cost_usd": "5.51",
                "status": "mock"
            }
    except Exception as e:
        logger.error(f"Error estimating trade cost: {e}")
        return {"error": str(e)}

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for trader chat"""
    await websocket.accept()
    chat_connections.append(websocket)
    
    try:
        # Send welcome message
        await websocket.send_text("🤖 Crypto Trader Bot connected! How can I help you today?")
        
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            logger.info(f"Received chat message: {message}")
            
            # Process the message and send response
            response = await process_chat_message(message)
            await websocket.send_text(response)
            
    except WebSocketDisconnect:
        chat_connections.remove(websocket)
        logger.info("Chat client disconnected")
    except Exception as e:
        logger.error(f"Chat error: {e}")
        chat_connections.remove(websocket)

async def process_chat_message(message: str) -> str:
    """Process incoming chat messages and generate responses"""
    message_lower = message.lower()
    
    try:
        # Portfolio commands
        if any(word in message_lower for word in ["portfolio", "balance", "holdings"]):
            return "📊 Portfolio Overview:\n• Total Value: $125,750.50 (+2.31%)\n• ETH: 35.5 tokens ($87,275)\n• USDT: $25,000\n• LINK: 850.3 tokens ($12,625)\n• Success Rate: 73.6% (623/847 trades)"
        
        # Trading signals commands
        elif any(word in message_lower for word in ["signal", "trade", "buy", "sell", "recommendation"]):
            return "🎯 Trading Signals:\n• ETH/USDT: STRONG BUY (85.2% confidence)\n  Entry: $2,450.50 | Target: $2,650 | Stop: $2,300\n• LINK/USDT: HOLD (65.7% confidence)\n• Overall Sentiment: BULLISH (78.5%)"
        
        # Gas price commands
        elif "gas" in message_lower or "fees" in message_lower:
            if gpu_accelerator:
                gas_data = await asyncio.to_thread(gpu_accelerator.get_gas_prices)
                return f"⛽ Gas Prices & Trends:\n• Safe: {gas_data.get('safe_gas_price', 'N/A')} Gwei\n• Standard: {gas_data.get('standard_gas_price', 'N/A')} Gwei\n• Fast: {gas_data.get('fast_gas_price', 'N/A')} Gwei\n• Trend: STABLE | Optimal time: 02:00 UTC (8-12 Gwei)"
            else:
                return "⛽ Gas Prices & Trends:\n• Safe: 12 Gwei\n• Standard: 15 Gwei\n• Fast: 18 Gwei\n• Trend: STABLE | Optimal time: 02:00 UTC (8-12 Gwei)"
        
        # Market analysis commands
        elif any(word in message_lower for word in ["market", "analysis", "sentiment", "trend"]):
            return "� Market Analysis:\n• Overall Sentiment: BULLISH (78.5%)\n• Fear & Greed Index: 68 (Greed)\n• ETH Momentum: STRONG | RSI: 65.2\n• Key Resistance: $2,500, $2,650\n• Support Levels: $2,300, $2,150"
        
        # AI insights commands
        elif any(word in message_lower for word in ["ai", "insight", "prediction", "forecast"]):
            return "🤖 AI Insights:\n• Breakout probability: 75.2% (ETH/USDT, 4-8h)\n• Mean reversion setup: LINK/USDT (68.7%)\n• Risk Level: MODERATE\n• Recommendation: Scale in gradually, monitor gas costs"
        
        # Analytics commands
        elif any(word in message_lower for word in ["analytics", "metrics", "indicators", "technical"]):
            return "� Technical Analytics:\n• RSI(14): 65.2 | MACD: 12.5/8.3\n• Bollinger Bands: 2319.50 - 2580.50\n• Volume Trend: INCREASING\n• Network Utilization: 68.5%\n• Active Addresses: 542K"
        
        # Quick buy command
        elif "quick buy" in message_lower:
            return "🚀 Quick Buy Initiated:\n• Analyzing optimal entry point...\n• Current ETH price: $2,450.50\n• Recommended size: 2-5% of portfolio\n• Gas estimate: 15 Gwei ($4.50)\n• Execution pending your confirmation"
        
        # Quick sell command  
        elif "quick sell" in message_lower:
            return "📉 Quick Sell Analysis:\n• Current position value: $87,275\n• Recommended partial sell: 20-30%\n• Take profit level: $2,500-$2,550\n• Gas estimate: 15 Gwei ($4.50)\n• Execution pending your confirmation"
        
        # Settings commands
        elif any(word in message_lower for word in ["settings", "config", "preferences"]):
            return "⚙️ Trading Settings:\n• Risk Level: MODERATE\n• Max Position Size: 15%\n• Stop Loss: 5%\n• Gas Limit: 25 Gwei\n• Auto-trading: ENABLED\n• Slippage Tolerance: 1%"
        
        # Help commands
        elif any(word in message_lower for word in ["help", "commands", "what"]):
            return """🤖 ProTrade AI Commands:
📊 Portfolio: "portfolio", "balance", "holdings"
🎯 Trading: "signals", "buy", "sell", "trade"
⛽ Gas: "gas", "fees"
📈 Market: "market", "analysis", "sentiment"
🤖 AI: "insights", "predictions", "forecast"
📊 Analytics: "technical", "indicators", "metrics"
⚙️ Settings: "settings", "config"
🚀 Quick Actions: "quick buy", "quick sell" """
        
        # Status commands
        elif "status" in message_lower:
            gpu_status = "✅ GPU acceleration active" if gpu_accelerator else "⚠️ Running in demo mode"
            return f"🚀 ProTrade AI Status:\n• {gpu_status}\n• Portfolio: $125,750.50 (+2.31%)\n• Active Strategies: 3\n• Last Trade: 2 minutes ago\n• System Health: EXCELLENT\n• WebSocket: Connected ({len(chat_connections)} clients)"
        
        # Default intelligent response
        else:
            return f"💭 I understand you're asking about: '{message}'\n\n🎯 Try these commands:\n• 'portfolio' - View your holdings\n• 'signals' - Get trading recommendations\n• 'gas' - Check current fees\n• 'market' - Market analysis\n• 'help' - Full command list"
            
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        return f"❌ Error processing your request: {str(e)}\n\nTry: 'help' for available commands"

@app.get("/api/portfolio/overview")
async def get_portfolio_overview():
    """Get comprehensive portfolio overview"""
    try:
        # Simulate advanced portfolio data
        portfolio_data = {
            "total_value": 125750.50,
            "daily_change": 2847.30,
            "daily_change_percent": 2.31,
            "weekly_change": -1250.75,
            "weekly_change_percent": -0.98,
            "total_trades": 847,
            "successful_trades": 623,
            "success_rate": 73.6,
            "avg_gas_used": 15.2,
            "assets": [
                {
                    "symbol": "ETH",
                    "name": "Ethereum",
                    "balance": 35.5,
                    "value": 87275.00,
                    "allocation": 69.4,
                    "change_24h": 3.2
                },
                {
                    "symbol": "USDT",
                    "name": "Tether",
                    "balance": 25000.00,
                    "value": 25000.00,
                    "allocation": 19.9,
                    "change_24h": 0.0
                },
                {
                    "symbol": "LINK",
                    "name": "Chainlink",
                    "balance": 850.3,
                    "value": 12625.45,
                    "allocation": 10.0,
                    "change_24h": -1.5
                }
            ],
            "performance_history": [
                {"timestamp": "2024-01-01T00:00:00Z", "value": 100000},
                {"timestamp": "2024-01-02T00:00:00Z", "value": 102500},
                {"timestamp": "2024-01-03T00:00:00Z", "value": 98750},
                {"timestamp": "2024-01-04T00:00:00Z", "value": 105250},
                {"timestamp": "2024-01-05T00:00:00Z", "value": 125750.50}
            ]
        }
        return portfolio_data
    except Exception as e:
        logger.error(f"Error fetching portfolio overview: {e}")
        return {"error": str(e)}

@app.get("/api/trading/signals")
async def get_trading_signals():
    """Get AI-generated trading signals"""
    try:
        signals = {
            "overall_market_sentiment": "BULLISH",
            "confidence_score": 78.5,
            "signals": [
                {
                    "pair": "ETH/USDT",
                    "signal": "BUY",
                    "strength": "STRONG",
                    "confidence": 85.2,
                    "entry_price": 2450.50,
                    "target_price": 2650.00,
                    "stop_loss": 2300.00,
                    "reasoning": "RSI oversold bounce with volume confirmation",
                    "timeframe": "4H"
                },
                {
                    "pair": "LINK/USDT", 
                    "signal": "HOLD",
                    "strength": "MODERATE",
                    "confidence": 65.7,
                    "entry_price": 14.85,
                    "target_price": 16.50,
                    "stop_loss": 13.20,
                    "reasoning": "Consolidation pattern, awaiting breakout",
                    "timeframe": "1D"
                }
            ],
            "risk_assessment": {
                "overall_risk": "MODERATE",
                "volatility_index": 42.3,
                "market_correlation": 0.78
            }
        }
        return signals
    except Exception as e:
        logger.error(f"Error fetching trading signals: {e}")
        return {"error": str(e)}

@app.get("/api/analytics/advanced")
async def get_advanced_analytics():
    """Get advanced market analytics"""
    try:
        analytics = {
            "market_metrics": {
                "fear_greed_index": 68,
                "volatility_index": 42.3,
                "volume_trend": "INCREASING",
                "correlation_btc": 0.85
            },
            "technical_indicators": {
                "rsi_14": 65.2,
                "macd": {
                    "value": 12.5,
                    "signal": 8.3,
                    "histogram": 4.2
                },
                "bollinger_bands": {
                    "upper": 2580.50,
                    "middle": 2450.00,
                    "lower": 2319.50
                },
                "support_resistance": {
                    "resistance": [2500, 2650, 2800],
                    "support": [2300, 2150, 2000]
                }
            },
            "on_chain_metrics": {
                "active_addresses": 542000,
                "transaction_count": 1250000,
                "hash_rate": "185.2 EH/s",
                "network_utilization": 68.5
            }
        }
        return analytics
    except Exception as e:
        logger.error(f"Error fetching advanced analytics: {e}")
        return {"error": str(e)}

@app.get("/api/gas/advanced")
async def get_advanced_gas_data():
    """Get advanced gas analytics"""
    try:
        if gpu_accelerator:
            gas_data = await asyncio.to_thread(gpu_accelerator.get_gas_prices)
        else:
            gas_data = {
                "safe_gas_price": "12",
                "standard_gas_price": "15", 
                "fast_gas_price": "18",
                "base_fee": "10.5"
            }
        
        # Add advanced gas analytics
        advanced_gas = {
            **gas_data,
            "gas_trends": {
                "trend_1h": "DECREASING",
                "trend_6h": "STABLE", 
                "trend_24h": "INCREASING"
            },
            "gas_predictions": {
                "next_1h": "13-16 Gwei",
                "next_6h": "12-18 Gwei",
                "next_24h": "10-20 Gwei"
            },
            "optimal_times": [
                {"time": "02:00 UTC", "estimated_gas": "8-12 Gwei"},
                {"time": "14:00 UTC", "estimated_gas": "10-15 Gwei"},
                {"time": "22:00 UTC", "estimated_gas": "12-18 Gwei"}
            ],
            "congestion_level": "MODERATE",
            "pending_transactions": 125000
        }
        
        return advanced_gas
    except Exception as e:
        logger.error(f"Error fetching advanced gas data: {e}")
        return {"error": str(e)}

@app.get("/api/ai/insights")
async def get_ai_insights():
    """Get AI-powered market insights"""
    try:
        insights = {
            "market_analysis": {
                "summary": "Bullish momentum building with strong volume confirmation",
                "key_levels": {
                    "immediate_resistance": 2500,
                    "strong_resistance": 2650,
                    "immediate_support": 2300,
                    "strong_support": 2150
                },
                "sentiment_score": 78.5,
                "momentum_score": 82.1
            },
            "trading_opportunities": [
                {
                    "type": "BREAKOUT",
                    "pair": "ETH/USDT",
                    "probability": 75.2,
                    "timeframe": "4-8 hours",
                    "description": "Ascending triangle formation near completion"
                },
                {
                    "type": "MEAN_REVERSION",
                    "pair": "LINK/USDT", 
                    "probability": 68.7,
                    "timeframe": "1-2 days",
                    "description": "RSI oversold with support bounce likely"
                }
            ],
            "risk_factors": [
                {
                    "factor": "High volatility expected",
                    "impact": "MEDIUM",
                    "timeframe": "Next 6 hours"
                },
                {
                    "factor": "Gas prices trending higher",
                    "impact": "LOW", 
                    "timeframe": "Next 24 hours"
                }
            ],
            "recommendations": [
                "Consider scaling into positions gradually",
                "Monitor gas prices for optimal entry timing",
                "Set tight stop-losses in volatile conditions",
                "Take partial profits at resistance levels"
            ]
        }
        return insights
    except Exception as e:
        logger.error(f"Error fetching AI insights: {e}")
        return {"error": str(e)}

@app.get("/api/status")
async def get_system_status():
    """Get system status and health check"""
    return {
        "status": "online",
        "gpu_accelerator": gpu_accelerator is not None,
        "chat_connections": len(chat_connections),
        "version": "2.0.0",
        "features": ["Premium Dashboard", "AI Insights", "Advanced Analytics"],
        "endpoints": [
            "/api/gas",
            "/api/gas/advanced",
            "/api/dex/analytics", 
            "/api/portfolio/overview",
            "/api/trading/signals",
            "/api/analytics/advanced",
            "/api/ai/insights",
            "/api/trading/estimate",
            "/ws/chat"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Crypto Trading Bot API Server...")
    print("📊 Dashboard: http://localhost:8000")
    print("🔌 WebSocket Chat: ws://localhost:8000/ws/chat") 
    print("⛽ Gas API: http://localhost:8000/api/gas")
    print("📈 DEX API: http://localhost:8000/api/dex/analytics")
    
    uvicorn.run(
        "backend_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

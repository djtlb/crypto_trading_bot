"""
WebSocket Manager for Real-time Trading Bot Updates
==================================================

Handles WebSocket connections for real-time market data, portfolio updates,
and trading notifications.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import ccxt

logger = logging.getLogger("WebSocketManager")

class ConnectionManager:
    """Manages WebSocket connections and real-time data broadcasting"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.market_data_task = None
        self.portfolio_update_task = None
        self.is_running = False
        
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
        
        # Start real-time updates if this is the first connection
        if len(self.active_connections) == 1 and not self.is_running:
            await self.start_real_time_updates()
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Remaining: {len(self.active_connections)}")
        
        # Stop updates if no connections remain
        if len(self.active_connections) == 0:
            self.stop_real_time_updates()
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSockets"""
        if not self.active_connections:
            return
            
        disconnected = set()
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_json(self, data: Dict):
        """Broadcast JSON data to all connected WebSockets"""
        message = json.dumps(data)
        await self.broadcast(message)
    
    async def start_real_time_updates(self):
        """Start real-time market and portfolio updates"""
        self.is_running = True
        
        # Start market data updates
        self.market_data_task = asyncio.create_task(self.market_data_loop())
        
        # Start portfolio updates
        self.portfolio_update_task = asyncio.create_task(self.portfolio_update_loop())
        
        logger.info("Started real-time WebSocket updates")
    
    def stop_real_time_updates(self):
        """Stop real-time updates"""
        self.is_running = False
        
        if self.market_data_task:
            self.market_data_task.cancel()
        
        if self.portfolio_update_task:
            self.portfolio_update_task.cancel()
        
        logger.info("Stopped real-time WebSocket updates")
    
    async def market_data_loop(self):
        """Continuously fetch and broadcast market data"""
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        
        # Initialize a simple exchange for market data (no auth needed)
        try:
            exchange = ccxt.binance({'enableRateLimit': True})
        except Exception as e:
            logger.error(f"Could not initialize market data exchange: {e}")
            return
        
        while self.is_running:
            try:
                market_updates = []
                
                for symbol in symbols:
                    try:
                        ticker = await asyncio.to_thread(exchange.fetch_ticker, symbol)
                        market_updates.append({
                            'symbol': symbol,
                            'price': ticker['last'],
                            'change': ticker['percentage'],
                            'volume': ticker['quoteVolume'],
                            'bid': ticker['bid'],
                            'ask': ticker['ask'],
                            'timestamp': datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"Failed to fetch {symbol}: {e}")
                        continue
                
                if market_updates:
                    await self.broadcast_json({
                        'type': 'market_data',
                        'data': market_updates,
                        'timestamp': datetime.now().isoformat()
                    })
                
                # Update every 5 seconds
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Market data loop error: {e}")
                await asyncio.sleep(10)
    
    async def portfolio_update_loop(self):
        """Continuously broadcast portfolio and bot status updates"""
        from utils.demo_data import demo_service
        
        while self.is_running:
            try:
                # Import here to avoid circular imports
                from api_server import trading_bot, demo_mode, bot_status
                
                if demo_mode:
                    # Send demo data
                    portfolio_data = demo_service.get_demo_portfolio_status()
                    strategy_data = demo_service.get_demo_strategies()
                    gpu_data = demo_service.get_demo_gpu_status()
                else:
                    # Send real data if available
                    if trading_bot:
                        try:
                            portfolio_data = trading_bot.portfolio_manager.get_portfolio_status()
                            
                            strategy_data = {}
                            for strategy_name, strategy_info in trading_bot.strategies.items():
                                strategy_data[strategy_name] = {
                                    "total_trades": strategy_info.get("trade_count", 0),
                                    "successful_trades": strategy_info.get("successful_trades", 0),
                                    "symbols": strategy_info.get("symbols", [])
                                }
                            
                            gpu_data = {
                                "gpu_available": trading_bot.gpu_accelerator.gpu_available if hasattr(trading_bot, 'gpu_accelerator') else False,
                                "use_numba": True,
                                "use_polars": True,
                                "use_opencl": False
                            }
                        except Exception as e:
                            logger.warning(f"Error getting real portfolio data: {e}")
                            continue
                    else:
                        continue
                
                await self.broadcast_json({
                    'type': 'portfolio_update',
                    'data': {
                        'portfolio': portfolio_data,
                        'strategies': strategy_data,
                        'gpu_status': gpu_data,
                        'bot_status': bot_status,
                        'timestamp': datetime.now().isoformat()
                    }
                })
                
                # Update every 15 seconds
                await asyncio.sleep(15)
                
            except Exception as e:
                logger.error(f"Portfolio update loop error: {e}")
                await asyncio.sleep(15)
    
    async def send_trade_notification(self, trade_data: Dict):
        """Send immediate trade execution notification"""
        await self.broadcast_json({
            'type': 'trade_notification',
            'data': trade_data,
            'timestamp': datetime.now().isoformat()
        })
    
    async def send_alert(self, message: str, alert_type: str = 'info'):
        """Send alert notification to all connected clients"""
        await self.broadcast_json({
            'type': 'alert',
            'data': {
                'message': message,
                'alert_type': alert_type,
                'timestamp': datetime.now().isoformat()
            }
        })
    
    async def send_strategy_update(self, strategy_name: str, update_data: Dict):
        """Send strategy-specific update"""
        await self.broadcast_json({
            'type': 'strategy_update',
            'data': {
                'strategy': strategy_name,
                'update': update_data,
                'timestamp': datetime.now().isoformat()
            }
        })

# Global connection manager instance
manager = ConnectionManager()

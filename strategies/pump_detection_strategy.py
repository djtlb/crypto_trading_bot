"""
Pump Detection Strategy
======================

Simple but effective pump detection strategy that monitors for rapid price increases
with volume spikes and executes quick trades with take profit and stop loss.
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger("PumpDetectionStrategy")

class PumpDetectionStrategy:
    """
    Strategy that detects pump patterns and executes trades with risk management
    """
    
    def __init__(self, exchange_handler, portfolio_manager, config=None):
        self.exchange_handler = exchange_handler
        self.portfolio_manager = portfolio_manager
        
        # Strategy configuration
        self.config = config or {}
        self.trading_pair = self.config.get('trading_pair', 'BTC-USD')
        self.trade_amount_usd = self.config.get('trade_amount_usd', 20)
        self.take_profit_percent = self.config.get('take_profit_percent', 1.5)
        self.stop_loss_percent = self.config.get('stop_loss_percent', 1.0)
        self.pump_threshold = self.config.get('pump_threshold', 0.8)  # % price increase
        self.volume_multiplier = self.config.get('volume_multiplier', 1.5)
        
        # Trading state
        self.in_trade = False
        self.buy_price = 0
        self.buy_time = None
        self.trade_count = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.total_profit = 0
        
    def detect_pump(self, df: pd.DataFrame) -> bool:
        """
        Detect pump pattern in price data
        
        Args:
            df: DataFrame with price and volume data
            
        Returns:
            bool: True if pump detected
        """
        try:
            if len(df) < 3:
                return False
            
            # Ensure we have the right columns
            if 'price' in df.columns:
                df['close'] = df['price'].astype(float)
            elif 'close' in df.columns:
                df['close'] = df['close'].astype(float)
            else:
                return False
                
            if 'size' in df.columns:
                df['volume'] = df['size'].astype(float)
            elif 'volume' in df.columns:
                df['volume'] = df['volume'].astype(float)
            else:
                return False
            
            # Get last two data points
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Calculate price difference percentage
            price_diff = (last['close'] - prev['close']) / prev['close'] * 100
            
            # Check for volume spike
            volume_spike = last['volume'] > prev['volume'] * self.volume_multiplier
            
            # Pump conditions
            is_pump = price_diff > self.pump_threshold and volume_spike
            
            if is_pump:
                logger.info(f"🚨 PUMP DETECTED! Price: +{price_diff:.2f}%, Volume spike: {volume_spike}")
            
            return is_pump
            
        except Exception as e:
            logger.error(f"Error in pump detection: {e}")
            return False
    
    def get_price_data(self, limit: int = 20) -> pd.DataFrame:
        """
        Get recent trade data for analysis
        
        Args:
            limit: Number of recent trades to fetch
            
        Returns:
            DataFrame with trade data
        """
        try:
            # Get recent trades
            trades = self.exchange_handler.exchange.fetch_trades(self.trading_pair, limit=limit)
            
            if not trades:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(trades)
            
            # Ensure we have the required columns
            if 'price' not in df.columns and 'last' in df.columns:
                df['price'] = df['last']
            if 'amount' in df.columns and 'size' not in df.columns:
                df['size'] = df['amount']
                
            return df.sort_values('timestamp').tail(limit)
            
        except Exception as e:
            logger.error(f"Error fetching price data: {e}")
            return pd.DataFrame()
    
    def get_current_price(self) -> float:
        """Get current price of the trading pair"""
        try:
            ticker = self.exchange_handler.exchange.fetch_ticker(self.trading_pair)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return 0.0
    
    def place_market_order(self, side: str, amount_usd: float) -> Dict:
        """
        Place a market order
        
        Args:
            side: 'buy' or 'sell'
            amount_usd: Amount in USD
            
        Returns:
            Order result
        """
        try:
            current_price = self.get_current_price()
            if current_price <= 0:
                raise Exception("Could not get current price")
            
            if side == 'buy':
                # For buying, calculate how much crypto we can buy with USD
                amount = amount_usd / current_price
                order = self.exchange_handler.exchange.create_market_buy_order(
                    self.trading_pair, 
                    amount,
                    None,
                    None,
                    {'quoteOrderQty': amount_usd}  # Buy with specific USD amount
                )
            else:
                # For selling, we need to calculate how much crypto to sell
                # This assumes we're selling the same USD amount we bought
                amount = amount_usd / current_price
                order = self.exchange_handler.exchange.create_market_sell_order(
                    self.trading_pair,
                    amount
                )
            
            logger.info(f"Order placed: {side} {amount:.6f} {self.trading_pair} at ~${current_price:.2f}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing {side} order: {e}")
            raise
    
    def execute_strategy(self) -> Dict:
        """
        Main strategy execution logic
        
        Returns:
            Dict with strategy execution results
        """
        try:
            result = {
                "action": "none",
                "message": "No action taken",
                "in_trade": self.in_trade,
                "current_price": 0,
                "gain_percent": 0
            }
            
            # Get price data
            df = self.get_price_data()
            current_price = self.get_current_price()
            result["current_price"] = current_price
            
            if not self.in_trade:
                # Look for pump signal
                if self.detect_pump(df):
                    try:
                        # Buy signal detected
                        order = self.place_market_order('buy', self.trade_amount_usd)
                        self.buy_price = current_price
                        self.buy_time = datetime.now()
                        self.in_trade = True
                        self.trade_count += 1
                        
                        result.update({
                            "action": "buy",
                            "message": f"🚨 Pump detected! Bought ${self.trade_amount_usd} worth at ${current_price:.2f}",
                            "order": order,
                            "in_trade": True
                        })
                        
                        logger.info(result["message"])
                        
                    except Exception as e:
                        result.update({
                            "action": "buy_failed",
                            "message": f"Failed to buy: {str(e)}",
                            "error": str(e)
                        })
                else:
                    result["message"] = "🔍 Monitoring for pump signals..."
                    
            else:
                # We're in a trade, check for exit conditions
                if self.buy_price > 0:
                    gain_percent = (current_price - self.buy_price) / self.buy_price * 100
                    result["gain_percent"] = gain_percent
                    
                    should_sell = False
                    sell_reason = ""
                    
                    if gain_percent >= self.take_profit_percent:
                        should_sell = True
                        sell_reason = f"💰 Take profit at +{gain_percent:.2f}%"
                        self.successful_trades += 1
                        
                    elif gain_percent <= -self.stop_loss_percent:
                        should_sell = True
                        sell_reason = f"🛑 Stop loss at {gain_percent:.2f}%"
                        self.failed_trades += 1
                        
                    if should_sell:
                        try:
                            order = self.place_market_order('sell', self.trade_amount_usd)
                            profit = (gain_percent / 100) * self.trade_amount_usd
                            self.total_profit += profit
                            
                            result.update({
                                "action": "sell",
                                "message": sell_reason,
                                "order": order,
                                "profit_usd": profit,
                                "in_trade": False
                            })
                            
                            # Reset trade state
                            self.in_trade = False
                            self.buy_price = 0
                            self.buy_time = None
                            
                            logger.info(f"{sell_reason} - Profit: ${profit:.2f}")
                            
                        except Exception as e:
                            result.update({
                                "action": "sell_failed",
                                "message": f"Failed to sell: {str(e)}",
                                "error": str(e)
                            })
                    else:
                        result["message"] = f"📈 In trade - Gain: {gain_percent:.2f}% (Target: +{self.take_profit_percent}%, Stop: -{self.stop_loss_percent}%)"
            
            return result
            
        except Exception as e:
            logger.error(f"Strategy execution error: {e}")
            return {
                "action": "error",
                "message": f"Strategy error: {str(e)}",
                "error": str(e)
            }
    
    def get_performance_metrics(self) -> Dict:
        """Get strategy performance metrics"""
        success_rate = (self.successful_trades / max(self.trade_count, 1)) * 100
        
        return {
            "total_trades": self.trade_count,
            "successful_trades": self.successful_trades,
            "failed_trades": self.failed_trades,
            "success_rate_percent": round(success_rate, 2),
            "total_profit_usd": round(self.total_profit, 2),
            "average_profit_per_trade": round(self.total_profit / max(self.trade_count, 1), 2),
            "currently_in_trade": self.in_trade,
            "current_position": {
                "buy_price": self.buy_price,
                "buy_time": self.buy_time.isoformat() if self.buy_time else None
            } if self.in_trade else None
        }

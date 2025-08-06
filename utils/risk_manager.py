"""
Risk Manager Module
==================

Manages the risk associated with trading operations.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("RiskManager")

class RiskManager:
    """Manages risk for trading operations"""
    
    def __init__(
        self, 
        exchange_handler, 
        portfolio_manager=None,
        stop_loss_percentage: float = 3.0,
        take_profit_percentage: float = 8.0,
        max_trades: int = 10
    ):
        """
        Initialize the risk manager
        
        Args:
            exchange_handler: The exchange handler instance
            portfolio_manager: The portfolio manager instance
            stop_loss_percentage: The percentage at which to trigger a stop loss
            take_profit_percentage: The percentage at which to take profit
            max_trades: The maximum number of concurrent trades
        """
        self.exchange_handler = exchange_handler
        self.portfolio_manager = portfolio_manager
        self.stop_loss_percentage = stop_loss_percentage
        self.take_profit_percentage = take_profit_percentage
        self.max_trades = max_trades
        self.active_trades = {}
    
    def can_open_trade(self, symbol: str, amount: float) -> bool:
        """
        Check if a new trade can be opened based on risk parameters
        
        Args:
            symbol: The trading symbol
            amount: The trade amount
            
        Returns:
            True if trade can be opened, False otherwise
        """
        # Check portfolio manager constraints first
        if self.portfolio_manager:
            if not self.portfolio_manager.can_open_trade(symbol, amount):
                return False
        
        # Check if maximum trades limit is reached
        if len(self.active_trades) >= self.max_trades:
            logger.warning(f"Maximum concurrent trades ({self.max_trades}) reached")
            return False
        
        # Check if we have enough balance
        base_currency, quote_currency = symbol.split('/')
        balance = self.exchange_handler.get_balance(quote_currency)
        
        if not balance or quote_currency not in balance:
            logger.warning(f"Could not retrieve balance for {quote_currency}")
            return False
        
        free_balance = balance[quote_currency]['free']
        ticker = self.exchange_handler.get_ticker(symbol)
        
        if not ticker or 'last' not in ticker:
            logger.warning(f"Could not retrieve ticker for {symbol}")
            return False
        
        estimated_cost = amount * ticker['last']
        
        if estimated_cost > free_balance:
            logger.warning(f"Insufficient balance. Need {estimated_cost} {quote_currency}, but have {free_balance}")
            return False
        
        return True
    
    def calculate_position_size(self, symbol: str, trade_amount: float, use_percentage: float = 100.0) -> float:
        """
        Calculate the position size based on risk parameters
        
        Args:
            symbol: The trading symbol
            trade_amount: The maximum trade amount
            use_percentage: The percentage of trade_amount to use (0-100)
            
        Returns:
            The calculated position size
        """
        base_currency, quote_currency = symbol.split('/')
        
        # Get recommended trade size from portfolio manager if available
        if self.portfolio_manager:
            recommended_amount = self.portfolio_manager.get_recommended_trade_size(symbol)
            trade_amount = min(trade_amount, recommended_amount)
        
        # Apply percentage limit
        adjusted_amount = trade_amount * (use_percentage / 100.0)
        
        # Get current price
        ticker = self.exchange_handler.get_ticker(symbol)
        if not ticker or 'last' not in ticker:
            logger.warning(f"Could not retrieve ticker for {symbol}")
            return 0
        
        current_price = ticker['last']
        
        # Calculate amount in base currency
        base_amount = adjusted_amount / current_price
        
        # Apply exchange minimum amount if needed
        markets = self.exchange_handler.exchange.markets
        if symbol in markets and 'limits' in markets[symbol] and 'amount' in markets[symbol]['limits']:
            min_amount = markets[symbol]['limits']['amount']['min']
            if base_amount < min_amount:
                logger.warning(f"Calculated amount {base_amount} is below minimum {min_amount}, using minimum")
                base_amount = min_amount
        
        # Round to appropriate precision
        if symbol in markets and 'precision' in markets[symbol] and 'amount' in markets[symbol]['precision']:
            precision = markets[symbol]['precision']['amount']
            base_amount = round(base_amount, precision)
        
        return base_amount
    
    def set_stop_loss(self, symbol: str, entry_price: float, position_size: float, order_type: str = 'market') -> Dict:
        """
        Set a stop loss for a position
        
        Args:
            symbol: The trading symbol
            entry_price: The entry price
            position_size: The position size
            order_type: The order type ('market' or 'limit')
            
        Returns:
            The stop loss order details
        """
        # Calculate stop loss price
        stop_loss_price = entry_price * (1 - self.stop_loss_percentage / 100.0)
        
        # Round to appropriate precision
        markets = self.exchange_handler.exchange.markets
        if symbol in markets and 'precision' in markets[symbol] and 'price' in markets[symbol]['precision']:
            precision = markets[symbol]['precision']['price']
            stop_loss_price = round(stop_loss_price, precision)
        
        logger.info(f"Setting stop loss for {symbol} at {stop_loss_price}")
        
        # For now, we don't actually place the order, just track it
        # In a real implementation, you might want to place the order or use exchange's stop loss features
        stop_loss_order = {
            'symbol': symbol,
            'type': 'stop_loss',
            'price': stop_loss_price,
            'amount': position_size
        }
        
        return stop_loss_order
    
    def set_take_profit(self, symbol: str, entry_price: float, position_size: float, order_type: str = 'limit') -> Dict:
        """
        Set a take profit for a position
        
        Args:
            symbol: The trading symbol
            entry_price: The entry price
            position_size: The position size
            order_type: The order type ('market' or 'limit')
            
        Returns:
            The take profit order details
        """
        # Calculate take profit price
        take_profit_price = entry_price * (1 + self.take_profit_percentage / 100.0)
        
        # Round to appropriate precision
        markets = self.exchange_handler.exchange.markets
        if symbol in markets and 'precision' in markets[symbol] and 'price' in markets[symbol]['precision']:
            precision = markets[symbol]['precision']['price']
            take_profit_price = round(take_profit_price, precision)
        
        logger.info(f"Setting take profit for {symbol} at {take_profit_price}")
        
        # For now, we don't actually place the order, just track it
        # In a real implementation, you might want to place the order or use exchange's take profit features
        take_profit_order = {
            'symbol': symbol,
            'type': 'take_profit',
            'price': take_profit_price,
            'amount': position_size
        }
        
        return take_profit_order
    
    def register_trade(self, symbol: str, order: Dict, stop_loss: Dict, take_profit: Dict) -> str:
        """
        Register a new trade with the risk manager
        
        Args:
            symbol: The trading symbol
            order: The order details
            stop_loss: The stop loss order details
            take_profit: The take profit order details
            
        Returns:
            The trade ID
        """
        if 'id' not in order:
            logger.warning("Cannot register trade without order ID")
            return ""
        
        trade_id = order['id']
        
        # Register with portfolio manager if available
        if self.portfolio_manager:
            # Estimate trade cost
            ticker = self.exchange_handler.get_ticker(symbol)
            if ticker and 'last' in ticker:
                trade_cost = order.get('amount', 0) * ticker['last']
                self.portfolio_manager.execute_trade(trade_id, trade_cost)
        
        self.active_trades[trade_id] = {
            'symbol': symbol,
            'order': order,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'status': 'open'
        }
        
        logger.info(f"Registered trade {trade_id} for {symbol}")
        return trade_id
    
    def check_trades(self) -> List[Dict]:
        """
        Check the status of all active trades and manage stop loss/take profit
        
        Returns:
            A list of trades that were closed
        """
        closed_trades = []
        
        for trade_id, trade in list(self.active_trades.items()):
            symbol = trade['symbol']
            order = trade['order']
            stop_loss = trade['stop_loss']
            take_profit = trade['take_profit']
            
            # Get current price
            ticker = self.exchange_handler.get_ticker(symbol)
            if not ticker or 'last' not in ticker:
                logger.warning(f"Could not retrieve ticker for {symbol}")
                continue
            
            current_price = ticker['last']
            
            # Check if stop loss is triggered
            if current_price <= stop_loss['price']:
                logger.info(f"Stop loss triggered for trade {trade_id} at {current_price}")
                
                # Execute stop loss
                # In a real implementation, you would place the actual sell order here
                
                self.active_trades[trade_id]['status'] = 'closed_stop_loss'
                closed_trades.append(self.active_trades[trade_id])
                del self.active_trades[trade_id]
            
            # Check if take profit is triggered
            elif current_price >= take_profit['price']:
                logger.info(f"Take profit triggered for trade {trade_id} at {current_price}")
                
                # Execute take profit
                # In a real implementation, you would place the actual sell order here
                
                self.active_trades[trade_id]['status'] = 'closed_take_profit'
                closed_trades.append(self.active_trades[trade_id])
                del self.active_trades[trade_id]
        
        return closed_trades
    
    def close_trade(self, trade_id: str) -> Dict:
        """
        Manually close a trade
        
        Args:
            trade_id: The trade ID
            
        Returns:
            The closed trade details
        """
        if trade_id not in self.active_trades:
            logger.warning(f"Trade {trade_id} not found")
            return {}
        
        trade = self.active_trades[trade_id]
        symbol = trade['symbol']
        
        # Calculate PnL for portfolio manager
        if self.portfolio_manager:
            # Get current price and calculate PnL
            ticker = self.exchange_handler.get_ticker(symbol)
            if ticker and 'last' in ticker:
                current_price = ticker['last']
                entry_price = trade['order'].get('price', current_price)
                amount = trade['order'].get('amount', 0)
                
                # Simple PnL calculation (for buy orders)
                pnl = (current_price - entry_price) * amount
                self.portfolio_manager.close_trade(trade_id, pnl)
        
        # Execute close
        # In a real implementation, you would place the actual sell order here
        
        trade['status'] = 'closed_manual'
        
        del self.active_trades[trade_id]
        logger.info(f"Manually closed trade {trade_id}")
        
        return trade

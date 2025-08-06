"""
Portfolio Manager Module
=======================

Manages the overall portfolio and ensures trading stays within budget limits.
"""

import logging
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("PortfolioManager")

class PortfolioManager:
    """Manages portfolio allocation and budget constraints"""
    
    def __init__(self, exchange_handler, total_budget: float = 50.0, config_path: str = None):
        """
        Initialize the portfolio manager
        
        Args:
            exchange_handler: The exchange handler instance
            total_budget: Total budget for trading
            config_path: Path to configuration file
        """
        self.exchange_handler = exchange_handler
        self.total_budget = total_budget
        self.used_budget = 0.0
        self.reserved_budget = 0.0
        self.active_trades = {}
        self.trade_history = []
        self.daily_pnl = 0.0
        self.daily_trade_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Trading limits
        self.max_concurrent_trades = self.config.get('trading', {}).get('max_concurrent_trades', 10)
        self.min_trade_amount = self.config.get('trading', {}).get('min_trade_amount', 3)
        self.max_trade_amount = self.config.get('trading', {}).get('max_trade_amount', 8)
        self.daily_loss_limit = self.config.get('risk_management', {}).get('daily_loss_limit', 10)
        self.max_drawdown = self.config.get('risk_management', {}).get('max_drawdown_percentage', 15)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        if not config_path:
            config_path = 'config/config.json'
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            return {}
    
    def _reset_daily_limits(self):
        """Reset daily limits if it's a new day"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_pnl = 0.0
            self.daily_trade_count = 0
            self.last_reset_date = current_date
            logger.info("Daily limits reset for new trading day")
    
    def can_open_trade(self, symbol: str, trade_amount: float) -> bool:
        """
        Check if a new trade can be opened
        
        Args:
            symbol: Trading symbol
            trade_amount: Proposed trade amount
            
        Returns:
            True if trade can be opened, False otherwise
        """
        self._reset_daily_limits()
        
        # Check if we have reached max concurrent trades
        if len(self.active_trades) >= self.max_concurrent_trades:
            logger.warning(f"Max concurrent trades ({self.max_concurrent_trades}) reached")
            return False
        
        # Check if trade amount is within limits
        if trade_amount < self.min_trade_amount:
            logger.warning(f"Trade amount {trade_amount} below minimum {self.min_trade_amount}")
            return False
        
        if trade_amount > self.max_trade_amount:
            logger.warning(f"Trade amount {trade_amount} above maximum {self.max_trade_amount}")
            return False
        
        # Check available budget
        available_budget = self.total_budget - self.used_budget - self.reserved_budget
        if trade_amount > available_budget:
            logger.warning(f"Insufficient budget. Need {trade_amount}, available {available_budget}")
            return False
        
        # Check daily loss limit
        if self.daily_pnl <= -self.daily_loss_limit:
            logger.warning(f"Daily loss limit ({self.daily_loss_limit}) reached")
            return False
        
        # Check exchange balance
        base_currency, quote_currency = symbol.split('/')
        balance = self.exchange_handler.get_balance(quote_currency)
        
        if not balance or quote_currency not in balance:
            logger.warning(f"Could not retrieve balance for {quote_currency}")
            return False
        
        free_balance = balance[quote_currency]['free']
        if trade_amount > free_balance:
            logger.warning(f"Insufficient exchange balance. Need {trade_amount}, have {free_balance}")
            return False
        
        return True
    
    def allocate_trade_budget(self, trade_id: str, amount: float) -> bool:
        """
        Allocate budget for a trade
        
        Args:
            trade_id: Unique trade identifier
            amount: Amount to allocate
            
        Returns:
            True if allocation successful, False otherwise
        """
        if not self.can_open_trade("", amount):  # Generic check
            return False
        
        # Reserve the budget
        self.reserved_budget += amount
        self.active_trades[trade_id] = {
            'allocated_amount': amount,
            'start_time': datetime.now(),
            'status': 'active'
        }
        
        logger.info(f"Allocated {amount} for trade {trade_id}")
        return True
    
    def execute_trade(self, trade_id: str, actual_amount: float) -> bool:
        """
        Execute a trade and update budget tracking
        
        Args:
            trade_id: Trade identifier
            actual_amount: Actual amount used in trade
            
        Returns:
            True if execution successful, False otherwise
        """
        if trade_id not in self.active_trades:
            logger.error(f"Trade {trade_id} not found in active trades")
            return False
        
        trade = self.active_trades[trade_id]
        allocated_amount = trade['allocated_amount']
        
        # Move from reserved to used budget
        self.reserved_budget -= allocated_amount
        self.used_budget += actual_amount
        
        # Update trade record
        trade['actual_amount'] = actual_amount
        trade['execute_time'] = datetime.now()
        trade['status'] = 'executed'
        
        self.daily_trade_count += 1
        
        logger.info(f"Executed trade {trade_id} with amount {actual_amount}")
        return True
    
    def close_trade(self, trade_id: str, pnl: float) -> bool:
        """
        Close a trade and update PnL tracking
        
        Args:
            trade_id: Trade identifier
            pnl: Profit/Loss from the trade
            
        Returns:
            True if close successful, False otherwise
        """
        if trade_id not in self.active_trades:
            logger.error(f"Trade {trade_id} not found in active trades")
            return False
        
        trade = self.active_trades[trade_id]
        actual_amount = trade.get('actual_amount', trade['allocated_amount'])
        
        # Update budgets
        self.used_budget -= actual_amount
        
        # Add PnL to available budget (if profit) or reduce total budget (if loss)
        if pnl > 0:
            # Profit increases available budget
            self.total_budget += pnl
        else:
            # Loss reduces total budget
            self.total_budget += pnl  # pnl is negative for losses
        
        # Update daily PnL
        self.daily_pnl += pnl
        
        # Move to trade history
        trade.update({
            'close_time': datetime.now(),
            'pnl': pnl,
            'status': 'closed'
        })
        
        self.trade_history.append(trade)
        del self.active_trades[trade_id]
        
        logger.info(f"Closed trade {trade_id} with PnL {pnl}")
        return True
    
    def get_portfolio_status(self) -> Dict:
        """
        Get current portfolio status
        
        Returns:
            Dictionary with portfolio information
        """
        self._reset_daily_limits()
        
        available_budget = self.total_budget - self.used_budget - self.reserved_budget
        
        return {
            'total_budget': self.total_budget,
            'used_budget': self.used_budget,
            'reserved_budget': self.reserved_budget,
            'available_budget': available_budget,
            'active_trades': len(self.active_trades),
            'max_concurrent_trades': self.max_concurrent_trades,
            'daily_pnl': self.daily_pnl,
            'daily_trade_count': self.daily_trade_count,
            'daily_loss_limit': self.daily_loss_limit,
            'utilization_percentage': ((self.used_budget + self.reserved_budget) / self.total_budget) * 100
        }
    
    def get_recommended_trade_size(self, symbol: str = None) -> float:
        """
        Get recommended trade size based on current portfolio state
        
        Args:
            symbol: Trading symbol (optional)
            
        Returns:
            Recommended trade size
        """
        available_budget = self.total_budget - self.used_budget - self.reserved_budget
        
        # Conservative sizing when we have many active trades
        active_trade_ratio = len(self.active_trades) / self.max_concurrent_trades
        
        if active_trade_ratio > 0.8:
            # Nearly at capacity, use smaller trades
            recommended_size = min(self.min_trade_amount, available_budget * 0.1)
        elif active_trade_ratio > 0.5:
            # Moderate capacity, use medium trades
            recommended_size = min(self.max_trade_amount * 0.7, available_budget * 0.2)
        else:
            # Low capacity, can use larger trades
            recommended_size = min(self.max_trade_amount, available_budget * 0.3)
        
        # Ensure it's within our limits
        recommended_size = max(self.min_trade_amount, recommended_size)
        recommended_size = min(self.max_trade_amount, recommended_size)
        
        return round(recommended_size, 2)
    
    def emergency_close_all(self) -> List[str]:
        """
        Emergency close all active trades (in case of major drawdown)
        
        Returns:
            List of trade IDs that were closed
        """
        closed_trades = []
        
        for trade_id in list(self.active_trades.keys()):
            # In a real implementation, you would place sell orders here
            logger.warning(f"Emergency closing trade {trade_id}")
            
            # Assume breakeven close for emergency
            self.close_trade(trade_id, 0.0)
            closed_trades.append(trade_id)
        
        logger.warning(f"Emergency closed {len(closed_trades)} trades")
        return closed_trades

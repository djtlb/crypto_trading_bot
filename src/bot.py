"""
Trading Bot Module
=================

Alternative bot implementation in src directory.
"""

import logging
from utils.exchange_handler import ExchangeHandler
from utils.risk_manager import RiskManager
from utils.portfolio_manager import PortfolioManager

logger = logging.getLogger("TradingBot")

class TradingBot:
    """Main trading bot class"""
    
    def __init__(self, config):
        """Initialize the trading bot"""
        self.config = config
        self.exchange_handler = None
        self.risk_manager = None
        self.portfolio_manager = None
        
    def initialize(self):
        """Initialize bot components"""
        # Initialize exchange handler
        self.exchange_handler = ExchangeHandler(
            self.config.get('exchange_id', 'binance'),
            self.config.get('api_key'),
            self.config.get('api_secret')
        )
        
        # Initialize portfolio manager
        self.portfolio_manager = PortfolioManager(
            self.exchange_handler,
            self.config.get('total_budget', 50)
        )
        
        # Initialize risk manager
        self.risk_manager = RiskManager(
            self.exchange_handler,
            self.portfolio_manager,
            stop_loss_percentage=self.config.get('stop_loss', 3),
            take_profit_percentage=self.config.get('take_profit', 8),
            max_trades=self.config.get('max_trades', 10)
        )
        
        logger.info("Trading bot initialized successfully")
    
    def start(self):
        """Start the trading bot"""
        if not self.exchange_handler:
            self.initialize()
        
        logger.info("Trading bot started")
    
    def stop(self):
        """Stop the trading bot"""
        logger.info("Trading bot stopped")
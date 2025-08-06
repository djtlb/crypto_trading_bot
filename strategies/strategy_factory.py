"""
Strategy Factory Module
======================

Factory for creating trading strategy instances.
"""

import logging
import importlib
from typing import Dict, Optional

logger = logging.getLogger("StrategyFactory")

class StrategyFactory:
    """Factory for creating trading strategy instances"""
    
    def __init__(self):
        """Initialize the strategy factory"""
        self.strategies = {
            'volatility_breakout': 'strategies.volatility_breakout.VolatilityBreakoutStrategy',
            'moving_average_cross': 'strategies.moving_average_cross.MovingAverageCrossStrategy',
            'rsi_strategy': 'strategies.rsi_strategy.RSIStrategy',
            'macd_strategy': 'strategies.macd_strategy.MACDStrategy'
        }
    
    def create_strategy(self, strategy_name: str, exchange_handler, risk_manager, **kwargs) -> Optional:
        """
        Create a strategy instance
        
        Args:
            strategy_name: The name of the strategy to create
            exchange_handler: The exchange handler instance
            risk_manager: The risk manager instance
            **kwargs: Additional arguments to pass to the strategy
            
        Returns:
            A strategy instance
        """
        if strategy_name not in self.strategies:
            logger.error(f"Strategy {strategy_name} not found")
            return None
        
        try:
            # Parse the module and class names
            module_path, class_name = self.strategies[strategy_name].rsplit('.', 1)
            
            # Import the module
            module = importlib.import_module(module_path)
            
            # Get the class
            strategy_class = getattr(module, class_name)
            
            # Create the instance
            strategy = strategy_class(exchange_handler, risk_manager, **kwargs)
            
            logger.info(f"Created strategy {strategy_name}")
            return strategy
        
        except (ImportError, AttributeError) as e:
            logger.error(f"Error creating strategy {strategy_name}: {str(e)}")
            return None

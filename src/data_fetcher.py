"""
Data Fetcher Module
==================

Fetches and manages market data from various sources.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("DataFetcher")

class DataFetcher:
    """Fetches market data from exchanges"""
    
    def __init__(self, exchange_handler):
        """
        Initialize the data fetcher
        
        Args:
            exchange_handler: Exchange handler instance
        """
        self.exchange_handler = exchange_handler
        self.data_cache = {}
        self.cache_duration = 60  # Cache data for 60 seconds
    
    def get_ohlcv_data(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> pd.DataFrame:
        """
        Get OHLCV data for a symbol
        
        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"{symbol}_{timeframe}_{limit}"
        
        # Check cache first
        if cache_key in self.data_cache:
            cached_data, timestamp = self.data_cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_duration:
                return cached_data
        
        # Fetch new data
        try:
            candles = self.exchange_handler.get_ohlcv(symbol, timeframe, limit)
            
            if not candles:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            
            # Cache the data
            self.data_cache[cache_key] = (df, datetime.now())
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_ticker_data(self, symbol: str) -> Dict:
        """
        Get ticker data for a symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with ticker information
        """
        try:
            return self.exchange_handler.get_ticker(symbol)
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}
    
    def get_multiple_tickers(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get ticker data for multiple symbols
        
        Args:
            symbols: List of trading symbols
            
        Returns:
            Dictionary mapping symbols to ticker data
        """
        tickers = {}
        for symbol in symbols:
            tickers[symbol] = self.get_ticker_data(symbol)
        return tickers
    
    def clear_cache(self):
        """Clear the data cache"""
        self.data_cache.clear()
        logger.info("Data cache cleared")
import numpy as np
import pandas as pd
import logging
from config import RSI_PERIOD, RSI_OVERSOLD, RSI_OVERBOUGHT, EMA_FAST, EMA_SLOW, MACD_SIGNAL

logger = logging.getLogger(__name__)

class TradingStrategy:
    def __init__(self):
        logger.info("Trading strategy initialized")
        
    def calculate_rsi(self, prices, period=RSI_PERIOD):
        """Calculate Relative Strength Index"""
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = np.mean(gain[:period])
        avg_loss = np.mean(loss[:period])
        
        for i in range(period, len(delta)):
            avg_gain = (avg_gain * (period - 1) + gain[i]) / period
            avg_loss = (avg_loss * (period - 1) + loss[i]) / period
            
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
        
    def calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]
        
    def calculate_macd(self, prices):
        """Calculate MACD"""
        ema_fast = pd.Series(prices).ewm(span=EMA_FAST, adjust=False).mean()
        ema_slow = pd.Series(prices).ewm(span=EMA_SLOW, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=MACD_SIGNAL, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]
        
    def analyze_market(self, historical_data):
        """Analyze market data and generate trading signals"""
        if not historical_data or len(historical_data) < 50:
            logger.warning("Not enough historical data for analysis")
            return "HOLD"
            
        # Extract closing prices
        close_prices = np.array([candle[4] for candle in historical_data])
        
        # Calculate indicators
        rsi = self.calculate_rsi(close_prices)
        macd_line, signal_line, histogram = self.calculate_macd(close_prices)
        
        # Generate trading signal
        signal = "HOLD"
        
        # RSI strategy
        if rsi < RSI_OVERSOLD:
            signal = "BUY"
            logger.info(f"RSI oversold condition: {rsi}")
        elif rsi > RSI_OVERBOUGHT:
            signal = "SELL"
            logger.info(f"RSI overbought condition: {rsi}")
            
        # MACD confirmation
        if histogram > 0 and macd_line > signal_line:
            if signal != "SELL":  # Don't override a SELL signal
                signal = "BUY"
                logger.info(f"MACD bullish crossover: {histogram}")
        elif histogram < 0 and macd_line < signal_line:
            if signal != "BUY":  # Don't override a BUY signal
                signal = "SELL"
                logger.info(f"MACD bearish crossover: {histogram}")
                
        logger.info(f"Analysis complete - Signal: {signal}, RSI: {rsi:.2f}, MACD Hist: {histogram:.6f}")
        return signal

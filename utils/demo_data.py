"""
Demo Data Service for Trading Bot Web Interface
===============================================

Provides realistic demo data when users don't have real exchange credentials
"""

import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class DemoDataService:
    """Provides demo data for testing the web interface"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.demo_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        self.base_prices = {
            'BTC/USDT': 45000.00,
            'ETH/USDT': 3200.00,
            'BNB/USDT': 320.00,
            'ADA/USDT': 0.45,
            'SOL/USDT': 110.00
        }
        self.demo_trades = []
        self.demo_portfolio = {
            'total_budget': 50.00,
            'available_budget': 35.20,
            'allocated_budget': 14.80,
            'active_trades': 3,
            'max_trades': 10,
            'daily_pnl': 2.30
        }
        self.demo_strategies = {
            'gpu_rsi_strategy': {
                'symbols': ['BTC/USDT', 'ETH/USDT', 'ADA/USDT'],
                'trade_count': 15,
                'successful_trades': 12,
                'failed_trades': 3,
                'last_execution': {'symbol': 'BTC/USDT', 'action': 'buy', 'amount': 5.50}
            },
            'gpu_volatility_breakout': {
                'symbols': ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'],
                'trade_count': 8,
                'successful_trades': 6,
                'failed_trades': 2,
                'last_execution': {'symbol': 'ETH/USDT', 'action': 'sell', 'amount': 3.20}
            },
            'gpu_moving_average_cross': {
                'symbols': ['BTC/USDT', 'SOL/USDT'],
                'trade_count': 5,
                'successful_trades': 5,
                'failed_trades': 0,
                'last_execution': {'symbol': 'SOL/USDT', 'action': 'buy', 'amount': 4.10}
            }
        }
        self._generate_demo_trades()
    
    def _generate_demo_trades(self):
        """Generate realistic demo trade history"""
        for i in range(25):
            symbol = random.choice(self.demo_symbols)
            side = random.choice(['buy', 'sell'])
            amount = round(random.uniform(3.0, 8.0), 2)
            price = self.base_prices[symbol] * random.uniform(0.98, 1.02)
            
            trade_time = self.start_time - timedelta(hours=random.randint(1, 72))
            
            trade = {
                'id': f'demo_{i:04d}',
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price,
                'status': random.choice(['closed', 'closed', 'closed', 'open']),
                'timestamp': trade_time.isoformat(),
                'datetime': trade_time.isoformat()
            }
            self.demo_trades.append(trade)
        
        # Sort by timestamp
        self.demo_trades.sort(key=lambda x: x['timestamp'], reverse=True)
    
    def get_demo_balance(self) -> Dict:
        """Get demo account balance"""
        return {
            'USDT': {'free': 35.20, 'used': 14.80, 'total': 50.00},
            'BTC': {'free': 0.00025, 'used': 0.00012, 'total': 0.00037},
            'ETH': {'free': 0.0055, 'used': 0.0023, 'total': 0.0078},
            'BNB': {'free': 0.0, 'used': 0.015, 'total': 0.015},
            'ADA': {'free': 0.0, 'used': 8.5, 'total': 8.5},
            'SOL': {'free': 0.0, 'used': 0.042, 'total': 0.042}
        }
    
    def get_demo_ticker(self, symbol: str) -> Dict:
        """Get demo ticker data for a symbol"""
        if symbol not in self.base_prices:
            return {}
        
        base_price = self.base_prices[symbol]
        current_price = base_price * random.uniform(0.995, 1.005)
        change = random.uniform(-5.0, 5.0)
        
        return {
            'symbol': symbol,
            'last': current_price,
            'bid': current_price * 0.999,
            'ask': current_price * 1.001,
            'high': current_price * 1.02,
            'low': current_price * 0.98,
            'percentage': change,
            'quoteVolume': random.uniform(1000000, 10000000),
            'timestamp': int(time.time() * 1000)
        }
    
    def get_demo_portfolio_status(self) -> Dict:
        """Get demo portfolio status"""
        # Add some random variation
        self.demo_portfolio['daily_pnl'] += random.uniform(-0.5, 0.5)
        self.demo_portfolio['available_budget'] = max(0, 
            self.demo_portfolio['available_budget'] + random.uniform(-1.0, 1.0))
        
        return self.demo_portfolio.copy()
    
    def get_demo_strategies(self) -> Dict:
        """Get demo strategy performance"""
        # Add some random updates
        for strategy_name, strategy in self.demo_strategies.items():
            if random.random() < 0.1:  # 10% chance to update
                strategy['trade_count'] += 1
                if random.random() < 0.75:  # 75% success rate
                    strategy['successful_trades'] += 1
                else:
                    strategy['failed_trades'] += 1
        
        return self.demo_strategies.copy()
    
    def get_demo_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get demo trade history"""
        return self.demo_trades[:limit]
    
    def place_demo_order(self, symbol: str, side: str, amount: float) -> Dict:
        """Place a demo order"""
        order_id = f'demo_order_{int(time.time())}'
        
        # Check if we have enough balance
        if side == 'buy' and amount > self.demo_portfolio['available_budget']:
            raise ValueError("Insufficient funds")
        
        # Create demo order
        ticker = self.get_demo_ticker(symbol)
        order = {
            'id': order_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': ticker['last'],
            'status': 'closed',
            'timestamp': datetime.now().isoformat(),
            'datetime': datetime.now().isoformat()
        }
        
        # Add to trade history
        self.demo_trades.insert(0, order)
        
        # Update portfolio
        if side == 'buy':
            self.demo_portfolio['available_budget'] -= amount
            self.demo_portfolio['allocated_budget'] += amount
        
        return order
    
    def get_demo_gpu_status(self) -> Dict:
        """Get demo GPU status"""
        return {
            'gpu_available': True,
            'use_opencl': False,
            'use_numba': True,
            'use_polars': True
        }
    
    def get_demo_benchmark_results(self) -> Dict:
        """Get demo benchmark results"""
        return {
            'gpu_available': True,
            'numba_available': True,
            'test_passed': True,
            'performance_improvement': '5-20x speedup with Numba JIT',
            'benchmark_time': datetime.now().isoformat(),
            'details': {
                'rolling_mean': 'SUCCESS - 8.5x faster',
                'rsi_calculation': 'SUCCESS - 12.3x faster', 
                'atr_calculation': 'SUCCESS - 15.7x faster',
                'gpu_memory': 'AMD RX 5700 XT detected',
                'fallback_mode': 'Numba JIT compilation'
            }
        }
    
    def get_demo_logs(self) -> List[str]:
        """Get demo system logs"""
        logs = [
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO - GPU acceleration initialized",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO - Numba JIT compilation active",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO - AMD RX 5700 XT GPU detected",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO - Portfolio manager started",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO - Multi-strategy trader initialized",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SUCCESS - RSI strategy executed: BTC/USDT buy $5.50",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO - Volatility breakout detected: ETH/USDT",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SUCCESS - Moving average cross: SOL/USDT buy $4.10",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO - Portfolio status: 3/10 active trades",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO - Daily P&L: +$2.30",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] WARNING - Rate limit approaching for exchange",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO - GPU calculations 12.3x faster than CPU",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SUCCESS - Stop loss triggered: ADA/USDT sell $3.25",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO - Risk manager: position size optimized",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO - WebSocket connection stable"
        ]
        return logs[-20:]  # Return last 20 logs

# Global demo service instance
demo_service = DemoDataService()

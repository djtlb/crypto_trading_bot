"""
Trading Dashboard Module
=======================

Simple web dashboard to monitor trading bot performance.
"""

import json
import time
from datetime import datetime
from typing import Dict, List

class TradingDashboard:
    """Simple dashboard for monitoring trading activities"""
    
    def __init__(self, portfolio_manager, multi_trader=None):
        """
        Initialize the dashboard
        
        Args:
            portfolio_manager: Portfolio manager instance
            multi_trader: Multi-strategy trader instance
        """
        self.portfolio_manager = portfolio_manager
        self.multi_trader = multi_trader
        self.start_time = datetime.now()
    
    def get_dashboard_data(self) -> Dict:
        """
        Get data for the dashboard
        
        Returns:
            Dictionary with dashboard data
        """
        portfolio_status = self.portfolio_manager.get_portfolio_status()
        
        # Basic portfolio metrics
        data = {
            'timestamp': datetime.now().isoformat(),
            'uptime': str(datetime.now() - self.start_time),
            'portfolio': portfolio_status,
            'performance': {
                'total_return': portfolio_status['total_budget'] - 50.0,  # Assuming $50 starting budget
                'return_percentage': ((portfolio_status['total_budget'] - 50.0) / 50.0) * 100,
                'active_trades': portfolio_status['active_trades'],
                'daily_pnl': portfolio_status['daily_pnl']
            }
        }
        
        # Add strategy performance if multi-trader is available
        if self.multi_trader:
            strategy_summary = self.multi_trader.get_trading_summary()
            data['strategies'] = strategy_summary['strategy_performance']
            data['overall_stats'] = strategy_summary['overall_stats']
        
        return data
    
    def save_dashboard_data(self, filename: str = 'dashboard_data.json'):
        """
        Save dashboard data to a JSON file
        
        Args:
            filename: Name of the file to save data to
        """
        data = self.get_dashboard_data()
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving dashboard data: {e}")
    
    def print_status(self):
        """Print current status to console"""
        data = self.get_dashboard_data()
        
        print("\n" + "="*50)
        print("CRYPTO TRADING BOT DASHBOARD")
        print("="*50)
        print(f"Uptime: {data['uptime']}")
        print(f"Timestamp: {data['timestamp']}")
        
        print("\nPORTFOLIO STATUS:")
        portfolio = data['portfolio']
        print(f"  Total Budget: ${portfolio['total_budget']:.2f}")
        print(f"  Available Budget: ${portfolio['available_budget']:.2f}")
        print(f"  Used Budget: ${portfolio['used_budget']:.2f}")
        print(f"  Reserved Budget: ${portfolio['reserved_budget']:.2f}")
        print(f"  Utilization: {portfolio['utilization_percentage']:.1f}%")
        
        print("\nTRADING STATUS:")
        print(f"  Active Trades: {portfolio['active_trades']}/{portfolio['max_concurrent_trades']}")
        print(f"  Daily PnL: ${portfolio['daily_pnl']:.2f}")
        print(f"  Daily Trades: {portfolio['daily_trade_count']}")
        
        print("\nPERFORMANCE:")
        perf = data['performance']
        print(f"  Total Return: ${perf['total_return']:.2f}")
        print(f"  Return %: {perf['return_percentage']:.2f}%")
        
        if 'strategies' in data:
            print("\nSTRATEGY PERFORMANCE:")
            for strategy_name, stats in data['strategies'].items():
                print(f"  {strategy_name}:")
                print(f"    Trades: {stats['total_trades']}")
                print(f"    Success Rate: {stats['success_rate']:.1f}%")
        
        print("="*50 + "\n")
    
    def create_simple_html_dashboard(self, filename: str = 'dashboard.html'):
        """
        Create a simple HTML dashboard
        
        Args:
            filename: Name of the HTML file to create
        """
        data = self.get_dashboard_data()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Crypto Trading Bot Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: inline-block; margin: 10px 15px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ font-size: 12px; color: #7f8c8d; }}
        .positive {{ color: #27ae60; }}
        .negative {{ color: #e74c3c; }}
        .neutral {{ color: #f39c12; }}
        h1 {{ color: #2c3e50; text-align: center; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
        .status-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Crypto Trading Bot Dashboard</h1>
        
        <div class="card">
            <h2>📊 Portfolio Overview</h2>
            <div class="status-grid">
                <div class="metric">
                    <div class="metric-value">${data['portfolio']['total_budget']:.2f}</div>
                    <div class="metric-label">Total Budget</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${data['portfolio']['available_budget']:.2f}</div>
                    <div class="metric-label">Available</div>
                </div>
                <div class="metric">
                    <div class="metric-value {'positive' if data['portfolio']['daily_pnl'] > 0 else 'negative' if data['portfolio']['daily_pnl'] < 0 else 'neutral'}">${data['portfolio']['daily_pnl']:.2f}</div>
                    <div class="metric-label">Daily PnL</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{data['portfolio']['utilization_percentage']:.1f}%</div>
                    <div class="metric-label">Utilization</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>📈 Trading Activity</h2>
            <div class="status-grid">
                <div class="metric">
                    <div class="metric-value">{data['portfolio']['active_trades']}</div>
                    <div class="metric-label">Active Trades</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{data['portfolio']['daily_trade_count']}</div>
                    <div class="metric-label">Daily Trades</div>
                </div>
                <div class="metric">
                    <div class="metric-value {'positive' if data['performance']['return_percentage'] > 0 else 'negative' if data['performance']['return_percentage'] < 0 else 'neutral'}">{data['performance']['return_percentage']:.2f}%</div>
                    <div class="metric-label">Total Return</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{data['uptime']}</div>
                    <div class="metric-label">Uptime</div>
                </div>
            </div>
        </div>
        """
        
        if 'strategies' in data:
            html_content += """
        <div class="card">
            <h2>🎯 Strategy Performance</h2>
            <div class="status-grid">
            """
            
            for strategy_name, stats in data['strategies'].items():
                html_content += f"""
                <div class="metric">
                    <div class="metric-value">{stats['success_rate']:.1f}%</div>
                    <div class="metric-label">{strategy_name.replace('_', ' ').title()}<br>({stats['total_trades']} trades)</div>
                </div>
                """
            
            html_content += """
            </div>
        </div>
            """
        
        html_content += f"""
        <div class="card">
            <h2>ℹ️ System Information</h2>
            <p><strong>Last Updated:</strong> {data['timestamp']}</p>
            <p><strong>Status:</strong> <span class="positive">● ACTIVE</span></p>
            <p><strong>Auto-refresh:</strong> Every 30 seconds</p>
        </div>
    </div>
</body>
</html>
        """
        
        try:
            with open(filename, 'w') as f:
                f.write(html_content)
        except Exception as e:
            print(f"Error creating HTML dashboard: {e}")

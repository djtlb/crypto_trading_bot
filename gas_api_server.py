"""
Gas API Server for Ethereum Gas Tracker
======================================

This module provides API endpoints for the Ethereum Gas Tracker.
It exposes gas prices and transaction cost estimates via a REST API.
"""

import sys
import os
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, render_template
from flask_cors import CORS

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GasAPI")

# Import the GPU accelerator
from utils.gpu_acceleration import gpu_accelerator

# Initialize Flask app
app = Flask(__name__, 
           static_folder='../frontend/static',
           template_folder='../frontend')
CORS(app)  # Enable CORS for all routes

# Cache for gas prices to avoid hitting API rate limits
gas_cache = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 60  # Cache duration in seconds
}

@app.route('/')
def index():
    """Render the gas tracker UI"""
    return render_template('gas_tracker.html')

@app.route('/api/gas/prices', methods=['GET'])
def get_gas_prices():
    """Get current Ethereum gas prices"""
    # Check if we have cached data that's still valid
    current_time = datetime.now().timestamp()
    if gas_cache['data'] and (current_time - gas_cache['timestamp'] < gas_cache['cache_duration']):
        logger.info("Returning cached gas prices")
        return jsonify(gas_cache['data'])
    
    # Fetch fresh data
    logger.info("Fetching fresh gas prices from Etherscan")
    gas_prices = gpu_accelerator.fetch_gas_prices()
    
    if "error" in gas_prices:
        return jsonify({"error": gas_prices["error"]}), 500
    
    # Update cache
    gas_cache['data'] = gas_prices
    gas_cache['timestamp'] = current_time
    
    return jsonify(gas_prices)

@app.route('/api/gas/transaction-costs/<int:gas_limit>', methods=['GET'])
def get_transaction_costs(gas_limit):
    """Get transaction cost estimates for a given gas limit"""
    if gas_limit <= 0 or gas_limit > 10000000:  # Sanity check
        return jsonify({"error": "Invalid gas limit"}), 400
    
    costs = gpu_accelerator.estimate_transaction_cost(gas_limit)
    
    if "error" in costs:
        return jsonify({"error": costs["error"]}), 500
    
    return jsonify(costs)

@app.route('/api/gas/estimates', methods=['GET'])
def get_common_estimates():
    """Get transaction cost estimates for common operations"""
    # Define common operations and their gas limits
    operations = {
        "eth_transfer": 21000,
        "erc20_transfer": 65000,
        "uniswap_swap": 150000,
        "nft_mint": 200000,
        "contract_deploy": 1000000
    }
    
    # Fetch gas prices first
    gas_prices = gpu_accelerator.fetch_gas_prices()
    if "error" in gas_prices:
        return jsonify({"error": gas_prices["error"]}), 500
    
    # Get estimates for each operation
    estimates = {
        "gas_prices": gas_prices,
        "estimates": {}
    }
    
    for op_name, gas_limit in operations.items():
        costs = gpu_accelerator.estimate_transaction_cost(gas_limit)
        if "error" not in costs:
            estimates["estimates"][op_name] = {
                "gas_limit": gas_limit,
                "costs": costs
            }
    
    return jsonify(estimates)

def start_server(host='0.0.0.0', port=5001, debug=False):
    """Start the Flask server"""
    logger.info(f"Starting Gas API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    start_server(debug=True)

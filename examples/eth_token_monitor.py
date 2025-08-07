#!/usr/bin/env python3
"""
ETH Token Monitor Example
========================

This example shows how to use the GPUAccelerator to monitor for new ETH-based tokens
and find arbitrage opportunities for WETH and USDT pairs.
"""

import sys
import os
import logging
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import GPU acceleration module
from utils.gpu_acceleration import GPUAccelerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                        'logs', 'eth_token_monitor.log'))
    ]
)

logger = logging.getLogger("ETHTokenMonitor")

def new_token_callback(token_data):
    """
    Callback function for processing new ETH-based tokens
    
    Args:
        token_data: Token data including profile and pair information
    """
    # Format and log the new token information
    token_symbol = token_data.get("baseToken", {}).get("symbol", "UNKNOWN")
    token_address = token_data.get("baseToken", {}).get("address", "")
    pair_address = token_data.get("pairCreated", {}).get("pairAddress", "")
    dex = token_data.get("pairCreated", {}).get("dex", "unknown")
    liquidity = token_data.get("liquidity", {}).get("usd", 0)
    timestamp = token_data.get("pairCreated", {}).get("timestamp", "")
    
    # Convert timestamp to readable format
    if timestamp:
        try:
            timestamp = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.debug(f"Error formatting timestamp: {e}")
            pass
    
    logger.info(f"NEW TOKEN DETECTED: {token_symbol}")
    logger.info(f"  Address: {token_address}")
    logger.info(f"  Pair Address: {pair_address}")
    logger.info(f"  DEX: {dex}")
    logger.info(f"  Liquidity: ${liquidity:.2f}")
    logger.info(f"  Created: {timestamp}")
    
    # Optionally look for arbitrage opportunities
    try:
        # Check for arbitrage opportunities if liquidity is sufficient
        if liquidity >= 50000:  # $50k minimum for arbitrage
            gpu_accel = GPUAccelerator()
            arb_opportunities = gpu_accel.find_arbitrage_opportunities(
                token_address=token_address,
                min_price_diff_percent=0.5  # 0.5% minimum price difference
            )
            
            if arb_opportunities.get("opportunitiesCount", 0) > 0:
                logger.info(f"  Found {arb_opportunities['opportunitiesCount']} arbitrage opportunities!")
                
                # Log the top opportunity
                top_opp = arb_opportunities["opportunities"][0]
                logger.info(f"  Best opportunity: {top_opp['buyDex']} -> {top_opp['sellDex']}")
                logger.info(f"  Price diff: {top_opp['priceDiffPercent']:.2f}%")
                logger.info(f"  Potential profit: ${top_opp['potentialProfit']:.2f}")
    except Exception as e:
        logger.error(f"Error checking arbitrage opportunities: {e}")

def main():
    """Main function to run the ETH token monitor"""
    logger.info("Starting ETH Token Monitor")
    
    # Initialize GPU accelerator
    gpu_accel = GPUAccelerator()
    
    # Check if GPU acceleration is available
    if gpu_accel.gpu_available:
        logger.info(f"GPU acceleration enabled: {gpu_accel.gpu_type}")
    else:
        logger.info("GPU acceleration not available, using CPU fallback")
    
    # Start monitoring for new ETH-based tokens
    logger.info("Setting up WebSocket connection to Moralis...")
    ws = gpu_accel.monitor_eth_based_tokens(
        callback=new_token_callback,
        min_liquidity_usd=10000  # $10k minimum liquidity
    )
    
    if not ws:
        logger.error("Failed to establish WebSocket connection")
        return
    
    logger.info("WebSocket connection established")
    logger.info("Monitoring for new ETH-based tokens... (press Ctrl+C to exit)")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down ETH Token Monitor...")
        if ws:
            ws.close()
    
    logger.info("ETH Token Monitor stopped")

if __name__ == "__main__":
    main()

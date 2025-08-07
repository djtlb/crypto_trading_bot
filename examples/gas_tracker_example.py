"""
Ethereum Gas Tracker Example
===========================

This example demonstrates how to use the GPU Accelerator's Ethereum Gas Tracker
to monitor gas prices and estimate transaction costs on Ethereum.
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GasTrackerExample")

# Import the GPU accelerator
from utils.gpu_acceleration import gpu_accelerator

def main():
    """Main function to demonstrate gas tracker usage"""
    logger.info("Ethereum Gas Tracker Example")
    logger.info("============================")
    
    # Check if GPU acceleration is available
    logger.info(f"GPU Acceleration available: {gpu_accelerator.gpu_available}")
    if gpu_accelerator.use_opencl:
        logger.info("Using OpenCL acceleration")
    elif gpu_accelerator.use_rocm:
        logger.info("Using ROCm acceleration")
    
    # Fetch current gas prices
    logger.info("\nFetching current Ethereum gas prices...")
    gas_prices = gpu_accelerator.fetch_gas_prices()
    
    if "error" in gas_prices:
        logger.error(f"Error fetching gas prices: {gas_prices['error']}")
        return
    
    # Display gas prices
    logger.info(f"\nCurrent Ethereum Gas Prices (Gwei) at {datetime.fromtimestamp(gas_prices['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}:")
    logger.info(f"Safe Gas Price: {gas_prices['safe_gas_price']} Gwei")
    logger.info(f"Standard Gas Price: {gas_prices['standard_gas_price']} Gwei")
    logger.info(f"Fast Gas Price: {gas_prices['fast_gas_price']} Gwei")
    logger.info(f"Base Fee: {gas_prices['base_fee']} Gwei")
    logger.info(f"Gas Used Ratio: {gas_prices['gas_used_ratio']}")
    
    # Estimate transaction costs for different operations
    logger.info("\nEstimating transaction costs:")
    
    # Simple ETH transfer (21,000 gas)
    eth_transfer = gpu_accelerator.estimate_transaction_cost(21000)
    logger.info("\nETH Transfer (21,000 gas):")
    log_transaction_costs(eth_transfer)
    
    # ERC-20 Token Transfer (~65,000 gas)
    erc20_transfer = gpu_accelerator.estimate_transaction_cost(65000)
    logger.info("\nERC-20 Token Transfer (~65,000 gas):")
    log_transaction_costs(erc20_transfer)
    
    # Uniswap Swap (~150,000 gas)
    uniswap_swap = gpu_accelerator.estimate_transaction_cost(150000)
    logger.info("\nUniswap Swap (~150,000 gas):")
    log_transaction_costs(uniswap_swap)
    
    # NFT Minting (~200,000 gas)
    nft_mint = gpu_accelerator.estimate_transaction_cost(200000)
    logger.info("\nNFT Minting (~200,000 gas):")
    log_transaction_costs(nft_mint)
    
    # Smart Contract Deployment (~1,000,000 gas)
    contract_deploy = gpu_accelerator.estimate_transaction_cost(1000000)
    logger.info("\nSmart Contract Deployment (~1,000,000 gas):")
    log_transaction_costs(contract_deploy)
    
    # Simulate trading strategy based on gas prices
    logger.info("\nSimulating trading strategy based on gas prices:")
    simulate_gas_based_trading(gas_prices)
    
def log_transaction_costs(costs):
    """Helper function to log transaction costs"""
    if "error" in costs:
        logger.error(f"Error: {costs['error']}")
        return
    
    logger.info(f"  Safe:     {costs['safe']['gas_price_gwei']} Gwei - Cost: {costs['safe']['cost_eth']:.6f} ETH (${costs['safe']['cost_usd']:.2f})")
    logger.info(f"  Standard: {costs['standard']['gas_price_gwei']} Gwei - Cost: {costs['standard']['cost_eth']:.6f} ETH (${costs['standard']['cost_usd']:.2f})")
    logger.info(f"  Fast:     {costs['fast']['gas_price_gwei']} Gwei - Cost: {costs['fast']['cost_eth']:.6f} ETH (${costs['fast']['cost_usd']:.2f})")

def simulate_gas_based_trading(gas_prices):
    """
    Simulate a trading strategy based on gas prices
    
    In real trading, gas prices can be a signal for network congestion,
    which often correlates with market activity and volatility.
    """
    gas_ratio = gas_prices['fast_gas_price'] / gas_prices['safe_gas_price']
    gas_used = gas_prices['gas_used_ratio']
    
    logger.info(f"Gas price ratio (Fast/Safe): {gas_ratio:.2f}")
    logger.info(f"Gas network utilization: {gas_used:.2f}")
    
    # Strategy logic:
    # - If gas prices are very high (ratio > 2) and network is congested: market may be volatile
    # - If gas prices are low (ratio < 1.5) and network is not congested: market may be stable
    
    if gas_ratio > 2.0 and gas_used > 0.8:
        logger.info("Market Signal: HIGH VOLATILITY - Gas prices are high and network is congested")
        logger.info("Trading Strategy: Consider reducing position sizes or delaying non-urgent transactions")
        logger.info("                 High fees might eat into trading profits")
        
    elif gas_ratio < 1.5 and gas_used < 0.5:
        logger.info("Market Signal: LOW VOLATILITY - Gas prices are low and network has capacity")
        logger.info("Trading Strategy: Good time for accumulation or portfolio rebalancing")
        logger.info("                 Transaction costs are optimal")
        
    else:
        logger.info("Market Signal: NORMAL CONDITIONS - Gas prices and network utilization are moderate")
        logger.info("Trading Strategy: Standard operations can proceed with normal caution")
    
    # Check for potential arbitrage opportunities
    if gas_prices['fast_gas_price'] < 30:  # Arbitrage may be profitable when gas is cheap
        logger.info("Arbitrage Opportunity: Gas prices are low enough for cross-DEX arbitrage to be profitable")
        logger.info("                      Consider running arbitrage scanner")

if __name__ == "__main__":
    main()

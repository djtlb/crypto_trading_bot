"""
DEX Strategy Example
=================

Example script showing how to use the DEX strategies.
"""

import os
import json
import logging
from web3 import Web3
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import time

# Local imports
from dex_utils.wallet_manager import WalletManager
from dex_strategies.strategy_factory import StrategyFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DEXStrategyExample")

def initialize_encryption():
    """Initialize encryption for securing private keys"""
    key_file = ".key"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            encryption_key = f.read()
    else:
        # Generate a new key
        encryption_key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(encryption_key)
        
        # Set restrictive permissions
        os.chmod(key_file, 0o600)
    
    return Fernet(encryption_key)

def run_strategy_example():
    """Run an example strategy"""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment variables
    rpc_url = os.getenv("ETH_RPC_URL", "https://ethereum.publicnode.com")
    private_key = os.getenv("PRIVATE_KEY", "")
    
    if not private_key:
        logger.error("Private key not found in environment variables")
        return
    
    try:
        # Initialize Web3
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        if not web3.is_connected():
            logger.error(f"Failed to connect to Ethereum RPC: {rpc_url}")
            return
        
        logger.info(f"Connected to Ethereum RPC")
        chain_id = web3.eth.chain_id
        logger.info(f"Chain ID: {chain_id}")
        
        # Initialize encryption
        fernet = initialize_encryption()
        
        # Initialize wallet manager
        wallet_manager = WalletManager(private_key=private_key, fernet=fernet)
        logger.info(f"Wallet address: {wallet_manager.address}")
        
        # Get ETH balance
        eth_balance = web3.eth.get_balance(wallet_manager.address)
        eth_balance_in_eth = web3.from_wei(eth_balance, "ether")
        logger.info(f"ETH balance: {eth_balance_in_eth} ETH")
        
        # Initialize strategy factory
        factory = StrategyFactory(web3, chain_id, wallet_manager)
        factory.set_encryption(fernet)
        
        # Define strategy parameters
        strategy_id = f"example_strategy_{int(time.time())}"
        strategy_type = "scalping"  # sniper, scalping, swing, arbitrage
        token_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # USDC on Ethereum
        dex_id = "uniswap_v2"
        base_token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # WETH on Ethereum
        amount = 0.01  # Amount in base token units (ETH)
        
        # Custom parameters for scalping strategy
        custom_params = {
            "price_check_interval": 10,
            "max_trades_per_day": 5,
            "max_gas_cost_percent": 2.0
        }
        
        # Create strategy
        logger.info(f"Creating {strategy_type} strategy for token {token_address}")
        result = factory.create_strategy(
            strategy_id=strategy_id,
            strategy_type=strategy_type,
            token_address=token_address,
            dex_id=dex_id,
            base_token_address=base_token_address,
            amount=amount,
            slippage=1.0,
            profit_target=3.0,
            stop_loss=1.5,
            trailing_stop=True,
            custom_params=custom_params
        )
        
        if not result["success"]:
            logger.error(f"Failed to create strategy: {result['message']}")
            return
        
        logger.info(f"Strategy created: {strategy_id}")
        
        # Start strategy
        start_result = factory.start_strategy(strategy_id)
        
        if not start_result["success"]:
            logger.error(f"Failed to start strategy: {start_result['message']}")
            return
        
        logger.info(f"Strategy started: {strategy_id}")
        
        # Run for some time
        logger.info(f"Running strategy for 60 seconds...")
        for i in range(6):
            time.sleep(10)
            
            # Get strategy status
            strategy_info = factory.get_strategy(strategy_id)
            if not strategy_info:
                logger.error(f"Failed to get strategy info")
                continue
            
            logger.info(f"Strategy status: {strategy_info['trade_state']}")
            
            # Execute strategy action
            execute_result = factory.execute_strategy_action(strategy_id, "execute")
            logger.info(f"Execute result: {execute_result['action']}")
        
        # Stop strategy
        stop_result = factory.stop_strategy(strategy_id, force_sell=True)
        
        if not stop_result["success"]:
            logger.error(f"Failed to stop strategy: {stop_result['message']}")
            return
        
        logger.info(f"Strategy stopped: {strategy_id}")
        
        # Get final performance
        performance = factory.get_strategy_performance(strategy_id)
        if performance["success"]:
            logger.info(f"Strategy performance: {json.dumps(performance['metrics'], indent=2)}")
        
        # Delete strategy
        delete_result = factory.delete_strategy(strategy_id)
        if delete_result["success"]:
            logger.info(f"Strategy deleted: {strategy_id}")
        
    except Exception as e:
        logger.error(f"Error running strategy example: {str(e)}")

if __name__ == "__main__":
    run_strategy_example()

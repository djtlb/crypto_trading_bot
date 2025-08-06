"""
DEX Trading Bot Flask Application
================================

Flask backend for connecting to decentralized exchanges and executing trades
via Web3 connections to EVM-compatible blockchains.
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
import time
import logging
from dotenv import load_dotenv
from web3 import Web3
import secrets
from cryptography.fernet import Fernet
from typing import Dict, List, Optional, Union

# Local imports
from dex_utils.wallet_manager import WalletManager
from dex_utils.dex_connector import DexConnector
from dex_utils.token_validator import TokenValidator
from dex_strategies.strategy_factory import StrategyFactory

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dex_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DEXBot")

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# Global variables
active_wallet = None
active_strategies = {}
connections = {}
encryption_key = None

# Supported DEXes and chains
SUPPORTED_DEXES = {
    "uniswap_v2": "Uniswap V2",
    "uniswap_v3": "Uniswap V3", 
    "pancakeswap_v2": "PancakeSwap V2",
    "sushiswap": "SushiSwap"
}

SUPPORTED_CHAINS = {
    "ethereum": {
        "name": "Ethereum Mainnet",
        "chain_id": 1,
        "rpc": os.getenv("ETH_RPC_URL", "https://ethereum.publicnode.com"),
        "explorer": "https://etherscan.io",
        "native_token": "ETH",
        "dexes": ["uniswap_v2", "uniswap_v3", "sushiswap"]
    },
    "bsc": {
        "name": "BNB Smart Chain",
        "chain_id": 56,
        "rpc": os.getenv("BSC_RPC_URL", "https://bsc-dataseed1.binance.org"),
        "explorer": "https://bscscan.com",
        "native_token": "BNB",
        "dexes": ["pancakeswap_v2"]
    },
    "polygon": {
        "name": "Polygon",
        "chain_id": 137,
        "rpc": os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com"),
        "explorer": "https://polygonscan.com",
        "native_token": "MATIC",
        "dexes": ["uniswap_v3", "sushiswap"]
    },
    "arbitrum": {
        "name": "Arbitrum One",
        "chain_id": 42161,
        "rpc": os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
        "explorer": "https://arbiscan.io",
        "native_token": "ETH",
        "dexes": ["uniswap_v3", "sushiswap"]
    }
}

def initialize_encryption():
    """Initialize encryption for securing private keys"""
    global encryption_key
    
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

def get_connection(chain_id):
    """Get or create Web3 connection for a specific chain"""
    global connections
    
    # Find chain config by chain_id
    chain_config = None
    for chain, config in SUPPORTED_CHAINS.items():
        if config["chain_id"] == chain_id:
            chain_config = config
            break
    
    if not chain_config:
        raise ValueError(f"Unsupported chain ID: {chain_id}")
    
    if chain_id not in connections:
        # Create new connection
        web3 = Web3(Web3.HTTPProvider(chain_config["rpc"]))
        if not web3.is_connected():
            raise ConnectionError(f"Failed to connect to {chain_config['name']} RPC")
        
        connections[chain_id] = web3
        logger.info(f"Connected to {chain_config['name']}")
    
    return connections[chain_id]

# Web Routes
@app.route("/")
def index():
    """Serve the main web interface"""
    return render_template("index.html")

# API Routes
@app.route("/api/status", methods=["GET"])
def get_status():
    """Get the current status of the DEX bot"""
    global active_wallet, active_strategies
    
    return jsonify({
        "wallet_connected": active_wallet is not None,
        "wallet_address": active_wallet.address if active_wallet else None,
        "chain_connections": [
            {"chain_id": chain_id, "connected": web3.is_connected()}
            for chain_id, web3 in connections.items()
        ],
        "active_strategies": len(active_strategies),
        "status": "running",
        "timestamp": int(time.time())
    })

@app.route("/api/connect_wallet", methods=["POST"])
def connect_wallet():
    """Connect to a wallet using address or private key"""
    global active_wallet
    
    data = request.json
    connection_type = data.get("type", "address")
    
    try:
        if connection_type == "private_key":
            # Connect with private key
            private_key = data.get("private_key")
            if not private_key:
                return jsonify({"success": False, "error": "Private key is required"}), 400
            
            # Initialize wallet manager with encryption
            fernet = initialize_encryption()
            active_wallet = WalletManager(private_key=private_key, fernet=fernet)
            
            return jsonify({
                "success": True,
                "address": active_wallet.address,
                "message": f"Successfully connected to wallet {active_wallet.address[:6]}...{active_wallet.address[-4:]}"
            })
            
        elif connection_type == "address":
            # Read-only mode with just an address
            address = data.get("address")
            if not address:
                return jsonify({"success": False, "error": "Wallet address is required"}), 400
            
            if not Web3.is_address(address):
                return jsonify({"success": False, "error": "Invalid Ethereum address"}), 400
                
            active_wallet = WalletManager(address=address)
            
            return jsonify({
                "success": True,
                "address": active_wallet.address,
                "message": f"Connected in read-only mode to {address[:6]}...{address[-4:]}",
                "read_only": True
            })
        
        else:
            return jsonify({"success": False, "error": "Invalid connection type"}), 400
            
    except Exception as e:
        logger.error(f"Wallet connection error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/disconnect_wallet", methods=["POST"])
def disconnect_wallet():
    """Disconnect the current wallet"""
    global active_wallet
    
    if active_wallet:
        address = active_wallet.address
        active_wallet = None
        return jsonify({
            "success": True,
            "message": f"Disconnected from wallet {address[:6]}...{address[-4:]}"
        })
    
    return jsonify({"success": False, "message": "No wallet connected"})

@app.route("/api/wallet_balances", methods=["GET"])
def get_wallet_balances():
    """Get token balances for the connected wallet"""
    global active_wallet
    
    if not active_wallet:
        return jsonify({"success": False, "error": "No wallet connected"}), 400
        
    chain_id = request.args.get("chain_id", 1, type=int)
    
    try:
        web3 = get_connection(chain_id)
        
        # Get ETH balance
        eth_balance = web3.eth.get_balance(active_wallet.address)
        eth_balance_in_eth = web3.from_wei(eth_balance, "ether")
        
        # Get custom token balances if specified
        token_addresses = request.args.get("tokens", "").split(",")
        token_balances = {}
        
        if token_addresses and token_addresses[0]:
            dex_connector = DexConnector(web3, chain_id)
            
            for token_address in token_addresses:
                if Web3.is_address(token_address):
                    balance = dex_connector.get_token_balance(
                        token_address, 
                        active_wallet.address
                    )
                    token_balances[token_address] = balance
        
        chain_name = "Unknown"
        native_token = "ETH"
        for _, config in SUPPORTED_CHAINS.items():
            if config["chain_id"] == chain_id:
                chain_name = config["name"]
                native_token = config["native_token"]
                break
        
        return jsonify({
            "success": True,
            "address": active_wallet.address,
            "chain_id": chain_id,
            "chain_name": chain_name,
            "native_balance": float(eth_balance_in_eth),
            "native_token": native_token,
            "token_balances": token_balances,
            "timestamp": int(time.time())
        })
        
    except Exception as e:
        logger.error(f"Error getting wallet balances: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/validate_token", methods=["GET"])
def validate_token():
    """Validate a token by checking if it's a honeypot"""
    token_address = request.args.get("token_address")
    chain_id = request.args.get("chain_id", 1, type=int)
    
    if not token_address:
        return jsonify({"success": False, "error": "Token address is required"}), 400
        
    if not Web3.is_address(token_address):
        return jsonify({"success": False, "error": "Invalid token address"}), 400
    
    try:
        web3 = get_connection(chain_id)
        validator = TokenValidator(web3, chain_id)
        result = validator.validate_token(token_address)
        
        return jsonify({
            "success": True,
            "token_address": token_address,
            "chain_id": chain_id,
            "is_valid": result["is_valid"],
            "is_honeypot": result["is_honeypot"],
            "can_buy": result["can_buy"],
            "can_sell": result["can_sell"],
            "details": result["details"]
        })
        
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/start_trade", methods=["POST"])
def start_trade():
    """Start a trading strategy"""
    global active_wallet, active_strategies
    
    if not active_wallet:
        return jsonify({"success": False, "error": "No wallet connected"}), 400
        
    if active_wallet.is_read_only:
        return jsonify({"success": False, "error": "Wallet is in read-only mode, cannot trade"}), 400
    
    data = request.json
    
    # Required parameters
    strategy_type = data.get("strategy_type")
    chain_id = data.get("chain_id")
    dex_id = data.get("dex_id")
    token_address = data.get("token_address")
    base_token_address = data.get("base_token_address", "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE")  # ETH by default
    amount = data.get("amount")
    
    # Optional parameters with defaults
    slippage = data.get("slippage", 1.0)  # 1% default slippage
    gas_price = data.get("gas_price", "auto")
    gas_limit = data.get("gas_limit", "auto")
    profit_target = data.get("profit_target", 5.0)  # 5% profit target
    stop_loss = data.get("stop_loss", 2.0)  # 2% stop loss
    trailing_stop = data.get("trailing_stop", False)
    
    # Strategy-specific parameters
    custom_params = data.get("custom_params", {})
    
    # Validate required parameters
    if not all([strategy_type, chain_id, dex_id, token_address, amount]):
        return jsonify({
            "success": False, 
            "error": "Missing required parameters"
        }), 400
    
    if strategy_type not in ["sniper", "scalping", "swing", "arbitrage"]:
        return jsonify({
            "success": False, 
            "error": f"Invalid strategy type: {strategy_type}"
        }), 400
    
    # For arbitrage strategy, we need target_dex_id
    if strategy_type == "arbitrage" and "target_dex_id" not in custom_params:
        return jsonify({
            "success": False,
            "error": "Arbitrage strategy requires target_dex_id in custom_params"
        }), 400
    
    # Generate unique strategy ID
    strategy_id = f"{strategy_type}_{token_address[:6]}_{int(time.time())}"
    
    try:
        # Get Web3 connection
        web3 = get_connection(chain_id)
        
        # Initialize strategy factory
        fernet = initialize_encryption()
        factory = StrategyFactory(web3, chain_id, active_wallet)
        factory.set_encryption(fernet)
        
        # Create strategy
        result = factory.create_strategy(
            strategy_id=strategy_id,
            strategy_type=strategy_type,
            token_address=token_address,
            dex_id=dex_id,
            base_token_address=base_token_address,
            amount=amount,
            slippage=slippage,
            gas_price=gas_price,
            gas_limit=gas_limit,
            profit_target=profit_target,
            stop_loss=stop_loss,
            trailing_stop=trailing_stop,
            custom_params=custom_params
        )
        
        if not result["success"]:
            return jsonify({
                "success": False,
                "error": result["message"]
            }), 400
        
        # Start the strategy
        start_result = factory.start_strategy(strategy_id)
        
        if not start_result["success"]:
            return jsonify({
                "success": False,
                "error": start_result["message"]
            }), 500
        
        # Store strategy factory
        active_strategies[strategy_id] = {
            "id": strategy_id,
            "factory": factory,
            "start_time": int(time.time()),
            "status": "running"
        }
        
        return jsonify({
            "success": True,
            "strategy_id": strategy_id,
            "message": f"Started {strategy_type} strategy for {token_address}",
            "status": "running",
            "details": result
        })
        
    except Exception as e:
        logger.error(f"Error starting strategy: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/stop_trade", methods=["POST"])
def stop_trade():
    """Stop a running trading strategy"""
    global active_strategies
    
    data = request.json
    strategy_id = data.get("strategy_id")
    force_sell = data.get("force_sell", False)
    
    if not strategy_id:
        return jsonify({"success": False, "error": "Strategy ID is required"}), 400
    
    if strategy_id not in active_strategies:
        return jsonify({"success": False, "error": "Strategy not found"}), 404
    
    try:
        # Get strategy factory
        factory = active_strategies[strategy_id]["factory"]
        
        # Stop the strategy
        result = factory.stop_strategy(strategy_id, force_sell)
        
        if not result["success"]:
            return jsonify({
                "success": False,
                "error": result["message"]
            }), 500
        
        # Update strategy status
        active_strategies[strategy_id]["status"] = "stopped"
        active_strategies[strategy_id]["stop_time"] = int(time.time())
        
        return jsonify({
            "success": True,
            "strategy_id": strategy_id,
            "message": f"Stopped strategy {strategy_id}",
            "status": "stopped",
            "details": result
        })
        
    except Exception as e:
        logger.error(f"Error stopping strategy {strategy_id}: {str(e)}")
        active_strategies[strategy_id]["status"] = "error"
        active_strategies[strategy_id]["error"] = str(e)
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/strategy_status", methods=["GET"])
def get_strategy_status():
    """Get the status of a specific trading strategy or all strategies"""
    global active_strategies
    
    strategy_id = request.args.get("strategy_id")
    
    if strategy_id:
        # Get specific strategy
        if strategy_id not in active_strategies:
            return jsonify({"success": False, "error": "Strategy not found"}), 404
        
        try:
            # Get strategy factory
            factory = active_strategies[strategy_id]["factory"]
            
            # Get strategy details
            strategy_info = factory.get_strategy(strategy_id)
            
            if not strategy_info:
                return jsonify({"success": False, "error": "Strategy not found in factory"}), 404
            
            # Add metadata from active_strategies
            for key in ["start_time", "stop_time", "status", "error"]:
                if key in active_strategies[strategy_id]:
                    strategy_info[key] = active_strategies[strategy_id][key]
            
            return jsonify({
                "success": True,
                "strategy": strategy_info
            })
            
        except Exception as e:
            logger.error(f"Error getting strategy status: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    else:
        # Get all strategies
        all_strategies = []
        
        for s_id, strategy_data in active_strategies.items():
            try:
                factory = strategy_data["factory"]
                strategy_info = factory.get_strategy(s_id)
                
                if strategy_info:
                    # Add metadata from active_strategies
                    for key in ["start_time", "stop_time", "status", "error"]:
                        if key in strategy_data:
                            strategy_info[key] = strategy_data[key]
                    
                    all_strategies.append(strategy_info)
                else:
                    # Strategy not found in factory, use basic info
                    basic_info = {
                        "id": s_id,
                        "status": strategy_data.get("status", "unknown")
                    }
                    all_strategies.append(basic_info)
                
            except Exception as e:
                logger.error(f"Error getting status for strategy {s_id}: {str(e)}")
                # Add basic info with error
                all_strategies.append({
                    "id": s_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return jsonify({
            "success": True,
            "strategies": all_strategies,
            "count": len(all_strategies)
        })

@app.route("/api/supported_chains", methods=["GET"])
def get_supported_chains():
    """Get list of supported chains"""
    return jsonify({
        "success": True,
        "chains": SUPPORTED_CHAINS
    })

@app.route("/api/supported_dexes", methods=["GET"])
def get_supported_dexes():
    """Get list of supported DEXes"""
    chain_id = request.args.get("chain_id")
    
    if chain_id:
        # Return DEXes for specific chain
        for chain, config in SUPPORTED_CHAINS.items():
            if str(config["chain_id"]) == chain_id:
                dexes = {
                    dex_id: SUPPORTED_DEXES[dex_id] 
                    for dex_id in config["dexes"]
                }
                return jsonify({
                    "success": True,
                    "chain_id": chain_id,
                    "chain_name": config["name"],
                    "dexes": dexes
                })
        
        return jsonify({"success": False, "error": "Chain not supported"}), 404
    
    # Return all DEXes
    return jsonify({
        "success": True,
        "dexes": SUPPORTED_DEXES
    })

@app.route("/api/get_gas_price", methods=["GET"])
def get_gas_price():
    """Get current gas price for a specific chain"""
    chain_id = request.args.get("chain_id", 1, type=int)
    
    try:
        web3 = get_connection(chain_id)
        
        # Get gas price based on chain
        if chain_id == 1:  # Ethereum
            # Get EIP-1559 gas info
            gas_info = web3.eth.fee_history(1, 'latest', [10, 50, 90])
            base_fee = web3.from_wei(gas_info['baseFeePerGas'][0], 'gwei')
            priority_fee = web3.from_wei(gas_info.get('reward', [[0]])[0][1], 'gwei')
            
            # Get legacy gas price
            gas_price = web3.from_wei(web3.eth.gas_price, 'gwei')
            
            # Convert Decimal to float before arithmetic operations
            base_fee_float = float(base_fee)
            priority_fee_float = float(priority_fee)
            
            return jsonify({
                "success": True,
                "chain_id": chain_id,
                "gas_price_gwei": float(gas_price),
                "base_fee_gwei": base_fee_float,
                "priority_fee_gwei": priority_fee_float,
                "estimated_fast_gwei": base_fee_float + priority_fee_float * 2,
                "estimated_slow_gwei": base_fee_float + priority_fee_float * 0.5,
                "eip1559_supported": True
            })
        else:
            # Get legacy gas price for other chains
            gas_price = web3.from_wei(web3.eth.gas_price, 'gwei')
            
            return jsonify({
                "success": True,
                "chain_id": chain_id,
                "gas_price_gwei": float(gas_price),
                "eip1559_supported": False
            })
            
    except Exception as e:
        logger.error(f"Error getting gas price: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/select_strategy", methods=["GET"])
def get_available_strategies():
    """Get list of available trading strategies and their parameters"""
    
    strategies = {
        "sniper": {
            "description": "Quick entry strategy for catching new token listings or dips",
            "parameters": {
                "token_address": "Token contract address to snipe",
                "base_token_address": "Base token to use for trading (default: chain's native token)",
                "amount": "Amount of base token to use",
                "slippage": "Slippage tolerance in percentage (default: 3.0)",
                "profit_target": "Profit target in percentage (default: 50.0)",
                "stop_loss": "Stop loss in percentage (default: 20.0)",
                "trailing_stop": "Whether to use trailing stop (default: true)",
                "auto_sell_time": "Automatically sell after this many seconds (0 = disabled)",
                "gas_multiplier": "Gas price multiplier to front-run others (default: 1.5)"
            }
        },
        "scalping": {
            "description": "Short-term strategy for small price movements",
            "parameters": {
                "token_address": "Token contract address to scalp",
                "base_token_address": "Base token to use for trading (default: chain's native token)",
                "amount": "Amount of base token to use",
                "slippage": "Slippage tolerance in percentage (default: 1.0)",
                "profit_target": "Profit target in percentage (default: 2.0)",
                "stop_loss": "Stop loss in percentage (default: 1.0)",
                "trailing_stop": "Whether to use trailing stop (default: true)",
                "price_check_interval": "Seconds between price checks (default: 5)",
                "max_trades_per_day": "Maximum number of trades per day (default: 10)",
                "max_gas_cost_percent": "Maximum gas cost as percentage of trade (default: 5.0)"
            }
        },
        "swing": {
            "description": "Medium-term strategy for larger price movements",
            "parameters": {
                "token_address": "Token contract address for swing trading",
                "base_token_address": "Base token to use for trading (default: chain's native token)",
                "amount": "Amount of base token to use",
                "slippage": "Slippage tolerance in percentage (default: 1.0)",
                "profit_target": "Profit target in percentage (default: 20.0)",
                "stop_loss": "Stop loss in percentage (default: 10.0)",
                "trailing_stop": "Whether to use trailing stop (default: true)",
                "price_check_interval": "Seconds between price checks (default: 300)",
                "trend_strength_threshold": "Minimum trend strength to enter (default: 5.0)",
                "max_hold_time": "Maximum hold time in seconds (default: 7 days)"
            }
        },
        "arbitrage": {
            "description": "Strategy for exploiting price differences between DEXes",
            "parameters": {
                "token_address": "Token contract address for arbitrage",
                "base_token_address": "Base token to use for trading (default: chain's native token)",
                "amount": "Amount of base token to use",
                "slippage": "Slippage tolerance in percentage (default: 0.5)",
                "custom_params": {
                    "target_dex_id": "Target DEX for the arbitrage (required)",
                    "min_profit_threshold": "Minimum profit percentage to execute (default: 1.0)",
                    "check_interval": "Seconds between opportunity checks (default: 30)",
                    "max_concurrent_arbs": "Maximum concurrent arbitrage operations (default: 1)"
                }
            }
        }
    }
    
    return jsonify({
        "success": True,
        "strategies": strategies
    })

@app.route("/api/price_feed", methods=["GET"])
def get_price_feed():
    """Get current price for a token"""
    token_address = request.args.get("token_address")
    chain_id = request.args.get("chain_id", 1, type=int)
    dex_id = request.args.get("dex_id", "uniswap_v2")
    base_token_address = request.args.get("base_token_address")
    
    if not token_address:
        return jsonify({"success": False, "error": "Token address is required"}), 400
        
    if not Web3.is_address(token_address):
        return jsonify({"success": False, "error": "Invalid token address"}), 400
    
    try:
        # Use native token if base token not specified
        if not base_token_address:
            base_token_address = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"  # Native token
        elif not Web3.is_address(base_token_address):
            return jsonify({"success": False, "error": "Invalid base token address"}), 400
        
        web3 = get_connection(chain_id)
        dex_connector = DexConnector(web3, chain_id)
        
        # Get token info
        token_info = dex_connector.get_token_info(token_address)
        base_token_info = dex_connector.get_token_info(base_token_address)
        
        # Get price (use a small amount to minimize price impact)
        if base_token_address == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            # If base token is native token, use 0.01
            amount_in = 10**16  # 0.01 ETH/BNB/etc
        else:
            # Otherwise use a small amount based on token decimals
            amount_in = 10**(base_token_info["decimals"]-2)  # 0.01 tokens
            
        try:
            # Try to get price impact from base to token
            price_data = dex_connector.get_price_impact(
                dex_id, 
                base_token_address, 
                token_address, 
                amount_in
            )
            
            if "error" in price_data:
                return jsonify({"success": False, "error": price_data["error"]}), 400
                
            token_price = price_data["amount_in_decimal"] / price_data["amount_out_decimal"] if price_data["amount_out_decimal"] > 0 else 0
            
            # Get price in the other direction too
            reverse_amount = 10**(token_info["decimals"]-2)  # 0.01 tokens
            reverse_price_data = dex_connector.get_price_impact(
                dex_id, 
                token_address, 
                base_token_address, 
                reverse_amount
            )
            
            if "error" not in reverse_price_data and reverse_price_data["amount_out_decimal"] > 0:
                reverse_token_price = reverse_price_data["amount_out_decimal"] / reverse_price_data["amount_in_decimal"]
                
                # Average the two prices for more accuracy
                token_price = (token_price + reverse_token_price) / 2
            
            return jsonify({
                "success": True,
                "token_address": token_address,
                "token_symbol": token_info["symbol"],
                "base_token_address": base_token_address,
                "base_token_symbol": base_token_info["symbol"],
                "price": token_price,
                "price_formatted": f"{token_price:.8f} {base_token_info['symbol']}",
                "timestamp": int(time.time())
            })
            
        except Exception as e:
            logger.error(f"Error getting token price: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
            
    except Exception as e:
        logger.error(f"Error in price feed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/quick_buy", methods=["POST"])
def quick_buy():
    """Quick buy a token with auto gas estimation"""
    global active_wallet
    
    if not active_wallet:
        return jsonify({"success": False, "error": "No wallet connected"}), 400
        
    if active_wallet.is_read_only:
        return jsonify({"success": False, "error": "Wallet is in read-only mode, cannot trade"}), 400
    
    data = request.json
    
    # Required parameters
    token_address = data.get("token_address")
    chain_id = data.get("chain_id", 1)
    dex_id = data.get("dex_id", "uniswap_v2")
    amount = data.get("amount")
    
    # Optional parameters
    base_token_address = data.get("base_token_address", "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE")
    slippage = data.get("slippage", 1.0)
    auto_gas = data.get("auto_gas", True)
    gas_speed = data.get("gas_speed", "fast")  # fast, average, slow
    gas_price = data.get("gas_price")
    gas_limit = data.get("gas_limit")
    
    # Validate parameters
    if not token_address or not Web3.is_address(token_address):
        return jsonify({"success": False, "error": "Valid token address is required"}), 400
        
    if not amount or float(amount) <= 0:
        return jsonify({"success": False, "error": "Amount must be greater than 0"}), 400
    
    try:
        # Get Web3 connection
        web3 = get_connection(chain_id)
        
        # Get token info
        dex_connector = DexConnector(web3, chain_id)
        base_token_info = dex_connector.get_token_info(base_token_address)
        
        # Convert amount to wei
        amount_wei = int(float(amount) * (10 ** base_token_info["decimals"]))
        
        # Auto-determine gas settings if requested
        if auto_gas:
            if chain_id == 1:  # Ethereum
                # Get EIP-1559 gas info
                gas_info = web3.eth.fee_history(1, 'latest', [10, 50, 90])
                base_fee = gas_info['baseFeePerGas'][0]
                priority_fee = gas_info.get('reward', [[0]])[0][1]
                
                if gas_speed == "fast":
                    max_fee = base_fee + priority_fee * 2
                    max_priority_fee = priority_fee * 2
                elif gas_speed == "average":
                    max_fee = base_fee + priority_fee
                    max_priority_fee = priority_fee
                else:  # slow
                    max_fee = base_fee + priority_fee // 2
                    max_priority_fee = priority_fee // 2
                
                gas_price = {
                    "maxFeePerGas": max_fee,
                    "maxPriorityFeePerGas": max_priority_fee
                }
            else:
                # Legacy gas price
                gas_multiplier = 1.2 if gas_speed == "fast" else (1.0 if gas_speed == "average" else 0.8)
                gas_price = int(web3.eth.gas_price * gas_multiplier)
        
        # Prepare buy transaction
        tx_data = dex_connector.prepare_buy_transaction(
            dex_id,
            token_address,
            amount_wei,
            active_wallet.address,
            slippage,
            base_token_address,
            gas_price,
            20  # 20 minutes deadline
        )
        
        if "error" in tx_data:
            return jsonify({"success": False, "error": tx_data.get("error")}), 400
        
        # Check if we need approval for ERC20 tokens
        if base_token_address != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            # Check if token is approved
            is_approved = active_wallet.is_token_approved(
                base_token_address,
                tx_data["router_address"],
                amount_wei,
                web3
            )
            
            if not is_approved:
                # Approve token
                logger.info(f"Approving {base_token_address} for trading on {dex_id}")
                approve_tx = active_wallet.approve_token(
                    base_token_address,
                    tx_data["router_address"],
                    2 ** 256 - 1,  # Unlimited approval
                    web3,
                    initialize_encryption()
                )
                
                # Wait for approval to be mined
                logger.info(f"Waiting for approval transaction to be mined: {approve_tx}")
                web3.eth.wait_for_transaction_receipt(approve_tx)
        
        # Send buy transaction
        fernet = initialize_encryption()
        tx_hash = active_wallet.send_transaction(
            tx_data["transaction"],
            web3,
            fernet
        )
        
        logger.info(f"Buy transaction sent: {tx_hash}")
        
        # Wait for transaction to be mined
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt["status"] == 1:
            # Get token balance after purchase
            token_balance = dex_connector.get_token_balance(
                token_address,
                active_wallet.address
            )
            
            return jsonify({
                "success": True,
                "transaction_hash": tx_hash,
                "block_number": receipt["blockNumber"],
                "gas_used": receipt["gasUsed"],
                "token_purchased": token_balance["token"]["symbol"],
                "amount_purchased": token_balance["balance"],
                "amount_purchased_wei": token_balance["balance_wei"],
                "message": f"Successfully purchased {token_balance['balance_formatted']}"
            })
        else:
            return jsonify({
                "success": False,
                "transaction_hash": tx_hash,
                "error": "Transaction failed on-chain"
            }), 400
        
    except Exception as e:
        logger.error(f"Error in quick buy: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/quick_sell", methods=["POST"])
def quick_sell():
    """Quick sell a token with auto gas estimation"""
    global active_wallet
    
    if not active_wallet:
        return jsonify({"success": False, "error": "No wallet connected"}), 400
        
    if active_wallet.is_read_only:
        return jsonify({"success": False, "error": "Wallet is in read-only mode, cannot trade"}), 400
    
    data = request.json
    
    # Required parameters
    token_address = data.get("token_address")
    chain_id = data.get("chain_id", 1)
    dex_id = data.get("dex_id", "uniswap_v2")
    
    # Optional parameters
    base_token_address = data.get("base_token_address", "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE")
    amount = data.get("amount")  # If not provided, sell all
    percent = data.get("percent")  # Sell percentage of holdings (0-100)
    slippage = data.get("slippage", 1.0)
    auto_gas = data.get("auto_gas", True)
    gas_speed = data.get("gas_speed", "fast")  # fast, average, slow
    gas_price = data.get("gas_price")
    
    # Validate parameters
    if not token_address or not Web3.is_address(token_address):
        return jsonify({"success": False, "error": "Valid token address is required"}), 400
    
    if amount and percent:
        return jsonify({
            "success": False, 
            "error": "Cannot specify both amount and percent. Choose one."
        }), 400
    
    try:
        # Get Web3 connection
        web3 = get_connection(chain_id)
        
        # Get token balance
        dex_connector = DexConnector(web3, chain_id)
        token_balance = dex_connector.get_token_balance(
            token_address,
            active_wallet.address
        )
        
        if int(token_balance["balance_wei"]) == 0:
            return jsonify({
                "success": False,
                "error": f"No {token_balance['token']['symbol']} tokens in wallet to sell"
            }), 400
        
        # Determine amount to sell
        if amount:
            # Convert provided amount to wei
            token_info = dex_connector.get_token_info(token_address)
            amount_wei = int(float(amount) * (10 ** token_info["decimals"]))
            
            if amount_wei > int(token_balance["balance_wei"]):
                return jsonify({
                    "success": False,
                    "error": f"Insufficient balance. You have {token_balance['balance_formatted']} but tried to sell {amount} {token_info['symbol']}"
                }), 400
        elif percent:
            # Calculate percentage of holdings
            if not (0 < float(percent) <= 100):
                return jsonify({
                    "success": False,
                    "error": "Percent must be between 0 and 100"
                }), 400
                
            amount_wei = int(int(token_balance["balance_wei"]) * float(percent) / 100)
        else:
            # Sell all tokens
            amount_wei = int(token_balance["balance_wei"])
        
        # Auto-determine gas settings if requested
        if auto_gas:
            if chain_id == 1:  # Ethereum
                # Get EIP-1559 gas info
                gas_info = web3.eth.fee_history(1, 'latest', [10, 50, 90])
                base_fee = gas_info['baseFeePerGas'][0]
                priority_fee = gas_info.get('reward', [[0]])[0][1]
                
                if gas_speed == "fast":
                    max_fee = base_fee + priority_fee * 2
                    max_priority_fee = priority_fee * 2
                elif gas_speed == "average":
                    max_fee = base_fee + priority_fee
                    max_priority_fee = priority_fee
                else:  # slow
                    max_fee = base_fee + priority_fee // 2
                    max_priority_fee = priority_fee // 2
                
                gas_price = {
                    "maxFeePerGas": max_fee,
                    "maxPriorityFeePerGas": max_priority_fee
                }
            else:
                # Legacy gas price
                gas_multiplier = 1.2 if gas_speed == "fast" else (1.0 if gas_speed == "average" else 0.8)
                gas_price = int(web3.eth.gas_price * gas_multiplier)
        
        # Prepare sell transaction
        tx_data = dex_connector.prepare_sell_transaction(
            dex_id,
            token_address,
            amount_wei,
            active_wallet.address,
            slippage,
            base_token_address,
            gas_price,
            20  # 20 minutes deadline
        )
        
        if "error" in tx_data:
            return jsonify({"success": False, "error": tx_data.get("error")}), 400
        
        # Check if token is approved for router
        is_approved = active_wallet.is_token_approved(
            token_address,
            tx_data["router_address"],
            amount_wei,
            web3
        )
        
        if not is_approved:
            # Approve token
            logger.info(f"Approving {token_address} for trading on {dex_id}")
            approve_tx = active_wallet.approve_token(
                token_address,
                tx_data["router_address"],
                2 ** 256 - 1,  # Unlimited approval
                web3,
                initialize_encryption()
            )
            
            # Wait for approval to be mined
            logger.info(f"Waiting for approval transaction to be mined: {approve_tx}")
            web3.eth.wait_for_transaction_receipt(approve_tx)
        
        # Send sell transaction
        fernet = initialize_encryption()
        tx_hash = active_wallet.send_transaction(
            tx_data["transaction"],
            web3,
            fernet
        )
        
        logger.info(f"Sell transaction sent: {tx_hash}")
        
        # Wait for transaction to be mined
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt["status"] == 1:
            # Get base token information
            base_token_info = dex_connector.get_token_info(base_token_address)
            
            # Format the amount that was sold
            token_info = dex_connector.get_token_info(token_address)
            amount_sold = amount_wei / (10 ** token_info["decimals"])
            
            # Calculate approximately how much base token was received
            amount_received = tx_data["estimation"]["amount_out_units"]
            
            return jsonify({
                "success": True,
                "transaction_hash": tx_hash,
                "block_number": receipt["blockNumber"],
                "gas_used": receipt["gasUsed"],
                "token_sold": token_info["symbol"],
                "amount_sold": amount_sold,
                "amount_sold_wei": str(amount_wei),
                "base_token_received": base_token_info["symbol"],
                "amount_received": amount_received,
                "amount_received_wei": tx_data["estimation"]["amount_out"],
                "message": f"Successfully sold {amount_sold} {token_info['symbol']} for approximately {amount_received} {base_token_info['symbol']}"
            })
        else:
            return jsonify({
                "success": False,
                "transaction_hash": tx_hash,
                "error": "Transaction failed on-chain"
            }), 400
        
    except Exception as e:
        logger.error(f"Error in quick sell: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Initialize encryption
    initialize_encryption()
    
    # Run the server
    app.run(host="0.0.0.0", port=5003, debug=True)

"""
DEX Connector Module
===================

Connects to decentralized exchanges and provides methods for trading
"""

from web3 import Web3
import json
import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

logger = logging.getLogger("DexConnector")

# Common ABIs
ERC20_ABI = [
    # Transfer function
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    # BalanceOf function
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    # Decimals function
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    # Symbol function
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    # Name function
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    # Approve function
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    # Allowance function
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

# Router ABIs for different DEXs
UNISWAP_V2_ROUTER_ABI = [
    # swapExactTokensForTokens
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    # swapExactETHForTokens
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactETHForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "payable",
        "type": "function"
    },
    # swapExactTokensForETH
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForETH",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    # getAmountsOut
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]

PANCAKESWAP_V2_ROUTER_ABI = UNISWAP_V2_ROUTER_ABI  # Same ABI for PancakeSwap V2

# Router addresses for different DEXs and chains
DEX_ROUTER_ADDRESSES = {
    # Ethereum Mainnet
    1: {
        "uniswap_v2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "sushiswap": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
    },
    # BSC Mainnet
    56: {
        "pancakeswap_v2": "0x10ED43C718714eb63d5aA57B78B54704E256024E"
    },
    # Polygon
    137: {
        "uniswap_v3": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        "sushiswap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        "quickswap": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"
    },
    # Arbitrum
    42161: {
        "uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "sushiswap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
    }
}

# Factory addresses for different DEXs and chains
DEX_FACTORY_ADDRESSES = {
    # Ethereum Mainnet
    1: {
        "uniswap_v2": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        "sushiswap": "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"
    },
    # BSC Mainnet
    56: {
        "pancakeswap_v2": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"
    },
    # Polygon
    137: {
        "sushiswap": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
        "quickswap": "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32"
    },
    # Arbitrum
    42161: {
        "sushiswap": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
    }
}

class DexConnector:
    """Connects to decentralized exchanges and provides trading functionality"""
    
    def __init__(self, web3: Web3, chain_id: int):
        """Initialize the DEX connector

        Args:
            web3: Web3 instance
            chain_id: Chain ID
        """
        self.web3 = web3
        self.chain_id = chain_id
        
        # Cache for token info
        self.token_cache = {}
        
        # Native token wrapping addresses (WETH, WBNB, etc.)
        self.wrapped_native_tokens = {
            1: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH on Ethereum
            56: "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",  # WBNB on BSC
            137: "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",  # WMATIC on Polygon
            42161: "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"  # WETH on Arbitrum
        }
        
        # Native token address representation
        self.native_token_address = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
    
    def get_router_address(self, dex_id: str) -> str:
        """Get router address for a specific DEX

        Args:
            dex_id: DEX identifier (e.g., 'uniswap_v2')

        Returns:
            Router contract address

        Raises:
            ValueError: If DEX not supported on the current chain
        """
        if self.chain_id not in DEX_ROUTER_ADDRESSES:
            raise ValueError(f"Chain ID {self.chain_id} not supported")
            
        if dex_id not in DEX_ROUTER_ADDRESSES[self.chain_id]:
            raise ValueError(f"{dex_id} not supported on chain ID {self.chain_id}")
            
        return DEX_ROUTER_ADDRESSES[self.chain_id][dex_id]
    
    def get_factory_address(self, dex_id: str) -> str:
        """Get factory address for a specific DEX

        Args:
            dex_id: DEX identifier (e.g., 'uniswap_v2')

        Returns:
            Factory contract address

        Raises:
            ValueError: If DEX not supported on the current chain
        """
        if self.chain_id not in DEX_FACTORY_ADDRESSES:
            raise ValueError(f"Chain ID {self.chain_id} not supported")
            
        if dex_id not in DEX_FACTORY_ADDRESSES[self.chain_id]:
            raise ValueError(f"{dex_id} not supported on chain ID {self.chain_id}")
            
        return DEX_FACTORY_ADDRESSES[self.chain_id][dex_id]
    
    def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """Get token information (name, symbol, decimals)

        Args:
            token_address: Token contract address

        Returns:
            Dictionary with token information
        """
        # Check if it's the native token
        if token_address.lower() == self.native_token_address.lower():
            native_symbols = {
                1: "ETH",
                56: "BNB",
                137: "MATIC",
                42161: "ETH"
            }
            
            return {
                "address": self.native_token_address,
                "name": native_symbols.get(self.chain_id, "ETH"),
                "symbol": native_symbols.get(self.chain_id, "ETH"),
                "decimals": 18
            }
            
        # Check cache first
        if token_address in self.token_cache:
            return self.token_cache[token_address]
            
        # Get token information from contract
        token_contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        
        try:
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            decimals = token_contract.functions.decimals().call()
            
            token_info = {
                "address": token_address,
                "name": name,
                "symbol": symbol,
                "decimals": decimals
            }
            
            # Cache the result
            self.token_cache[token_address] = token_info
            
            return token_info
            
        except Exception as e:
            logger.error(f"Error getting token info for {token_address}: {e}")
            
            # Return placeholder information
            return {
                "address": token_address,
                "name": "Unknown Token",
                "symbol": "???",
                "decimals": 18
            }
    
    def get_token_balance(self, token_address: str, wallet_address: str) -> Dict[str, Any]:
        """Get token balance for a wallet

        Args:
            token_address: Token contract address
            wallet_address: Wallet address

        Returns:
            Dictionary with token balance information
        """
        wallet_address = Web3.to_checksum_address(wallet_address)
        
        # Get token information
        token_info = self.get_token_info(token_address)
        
        # Check if it's the native token
        if token_address.lower() == self.native_token_address.lower():
            balance_wei = self.web3.eth.get_balance(wallet_address)
            balance = balance_wei / (10 ** 18)
            
            return {
                "token": token_info,
                "balance_wei": str(balance_wei),
                "balance": balance,
                "balance_formatted": f"{balance:.6f} {token_info['symbol']}"
            }
        
        # Get token balance
        token_contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        
        try:
            balance_wei = token_contract.functions.balanceOf(wallet_address).call()
            balance = balance_wei / (10 ** token_info["decimals"])
            
            return {
                "token": token_info,
                "balance_wei": str(balance_wei),
                "balance": balance,
                "balance_formatted": f"{balance:.6f} {token_info['symbol']}"
            }
            
        except Exception as e:
            logger.error(f"Error getting token balance for {token_address}: {e}")
            return {
                "token": token_info,
                "balance_wei": "0",
                "balance": 0,
                "balance_formatted": f"0 {token_info['symbol']}",
                "error": str(e)
            }
    
    def get_price_impact(
        self, 
        dex_id: str, 
        token_in_address: str, 
        token_out_address: str, 
        amount_in: int
    ) -> Dict[str, Any]:
        """Calculate price impact for a swap

        Args:
            dex_id: DEX identifier (e.g., 'uniswap_v2')
            token_in_address: Input token address
            token_out_address: Output token address
            amount_in: Input amount in wei

        Returns:
            Dictionary with price impact information
        """
        router_address = self.get_router_address(dex_id)
        router_abi = UNISWAP_V2_ROUTER_ABI
        
        # Get price for current amount
        try:
            router_contract = self.web3.eth.contract(
                address=router_address,
                abi=router_abi
            )
            
            # Create the path
            path = [
                Web3.to_checksum_address(token_in_address if token_in_address != self.native_token_address else self.wrapped_native_tokens[self.chain_id]),
                Web3.to_checksum_address(token_out_address if token_out_address != self.native_token_address else self.wrapped_native_tokens[self.chain_id])
            ]
            
            # Get amounts out for current amount
            amounts_out_current = router_contract.functions.getAmountsOut(amount_in, path).call()
            current_out = amounts_out_current[1]
            
            # Get amounts out for smaller amount (1% of current)
            small_amount_in = amount_in // 100
            amounts_out_small = router_contract.functions.getAmountsOut(small_amount_in, path).call()
            small_out = amounts_out_small[1]
            
            # Calculate price impact
            expected_out_scaled = small_out * 100
            price_impact = (expected_out_scaled - current_out) / expected_out_scaled * 100
            
            # Get token info
            token_in_info = self.get_token_info(token_in_address)
            token_out_info = self.get_token_info(token_out_address)
            
            # Calculate prices
            amount_in_decimal = amount_in / (10 ** token_in_info["decimals"])
            amount_out_decimal = current_out / (10 ** token_out_info["decimals"])
            price_per_token = amount_in_decimal / amount_out_decimal if amount_out_decimal > 0 else 0
            
            return {
                "amount_in": amount_in,
                "amount_in_decimal": amount_in_decimal,
                "amount_out": current_out,
                "amount_out_decimal": amount_out_decimal,
                "price_per_token": price_per_token,
                "price_impact_percent": price_impact,
                "path": path
            }
            
        except Exception as e:
            logger.error(f"Error calculating price impact: {e}")
            return {
                "error": str(e),
                "price_impact_percent": 100  # Assume worst case
            }
    
    def estimate_buy(
        self, 
        dex_id: str, 
        token_address: str, 
        amount_in: int,
        slippage: float = 1.0,
        base_token_address: str = None
    ) -> Dict[str, Any]:
        """Estimate buying a token

        Args:
            dex_id: DEX identifier (e.g., 'uniswap_v2')
            token_address: Token to buy
            amount_in: Input amount in wei
            slippage: Slippage percentage
            base_token_address: Base token address (default is native token)

        Returns:
            Dictionary with buy estimation details
        """
        # Use native token if base token not specified
        if not base_token_address:
            base_token_address = self.native_token_address
            
        # Get price impact
        price_data = self.get_price_impact(dex_id, base_token_address, token_address, amount_in)
        
        if "error" in price_data:
            return price_data
            
        # Calculate minimum amount out with slippage
        amount_out = price_data["amount_out"]
        min_amount_out = int(amount_out * (1 - slippage / 100))
        
        # Get token information
        token_info = self.get_token_info(token_address)
        base_token_info = self.get_token_info(base_token_address)
        
        # Calculate amounts in token units
        amount_in_units = amount_in / (10 ** base_token_info["decimals"])
        amount_out_units = amount_out / (10 ** token_info["decimals"])
        min_amount_out_units = min_amount_out / (10 ** token_info["decimals"])
        
        return {
            "token_address": token_address,
            "token_symbol": token_info["symbol"],
            "base_token_address": base_token_address,
            "base_token_symbol": base_token_info["symbol"],
            "amount_in": amount_in,
            "amount_in_units": amount_in_units,
            "amount_out": amount_out,
            "amount_out_units": amount_out_units,
            "min_amount_out": min_amount_out,
            "min_amount_out_units": min_amount_out_units,
            "price_impact_percent": price_data["price_impact_percent"],
            "path": price_data["path"],
            "slippage": slippage
        }
    
    def estimate_sell(
        self, 
        dex_id: str, 
        token_address: str, 
        amount_in: int,
        slippage: float = 1.0,
        base_token_address: str = None
    ) -> Dict[str, Any]:
        """Estimate selling a token

        Args:
            dex_id: DEX identifier (e.g., 'uniswap_v2')
            token_address: Token to sell
            amount_in: Input amount in wei
            slippage: Slippage percentage
            base_token_address: Base token address (default is native token)

        Returns:
            Dictionary with sell estimation details
        """
        # Use native token if base token not specified
        if not base_token_address:
            base_token_address = self.native_token_address
            
        # Get price impact
        price_data = self.get_price_impact(dex_id, token_address, base_token_address, amount_in)
        
        if "error" in price_data:
            return price_data
            
        # Calculate minimum amount out with slippage
        amount_out = price_data["amount_out"]
        min_amount_out = int(amount_out * (1 - slippage / 100))
        
        # Get token information
        token_info = self.get_token_info(token_address)
        base_token_info = self.get_token_info(base_token_address)
        
        # Calculate amounts in token units
        amount_in_units = amount_in / (10 ** token_info["decimals"])
        amount_out_units = amount_out / (10 ** base_token_info["decimals"])
        min_amount_out_units = min_amount_out / (10 ** base_token_info["decimals"])
        
        return {
            "token_address": token_address,
            "token_symbol": token_info["symbol"],
            "base_token_address": base_token_address,
            "base_token_symbol": base_token_info["symbol"],
            "amount_in": amount_in,
            "amount_in_units": amount_in_units,
            "amount_out": amount_out,
            "amount_out_units": amount_out_units,
            "min_amount_out": min_amount_out,
            "min_amount_out_units": min_amount_out_units,
            "price_impact_percent": price_data["price_impact_percent"],
            "path": price_data["path"],
            "slippage": slippage
        }
    
    def prepare_buy_transaction(
        self,
        dex_id: str,
        token_address: str,
        amount_in: int,
        wallet_address: str,
        slippage: float = 1.0,
        base_token_address: str = None,
        gas_price: Optional[int] = None,
        deadline_minutes: int = 20
    ) -> Dict[str, Any]:
        """Prepare a transaction to buy a token

        Args:
            dex_id: DEX identifier (e.g., 'uniswap_v2')
            token_address: Token to buy
            amount_in: Input amount in wei
            wallet_address: Wallet address
            slippage: Slippage percentage
            base_token_address: Base token address (default is native token)
            gas_price: Gas price in wei (optional)
            deadline_minutes: Transaction deadline in minutes

        Returns:
            Dictionary with transaction details
        """
        # Use native token if base token not specified
        if not base_token_address:
            base_token_address = self.native_token_address
        
        # Get buy estimation
        estimation = self.estimate_buy(dex_id, token_address, amount_in, slippage, base_token_address)
        
        if "error" in estimation:
            return estimation
        
        # Get router address and ABI
        router_address = self.get_router_address(dex_id)
        router_abi = UNISWAP_V2_ROUTER_ABI
        
        # Create router contract
        router_contract = self.web3.eth.contract(
            address=router_address,
            abi=router_abi
        )
        
        # Set deadline
        deadline = self.web3.eth.get_block('latest')['timestamp'] + (deadline_minutes * 60)
        
        # Prepare transaction parameters
        tx_params = {
            'from': wallet_address,
            'nonce': self.web3.eth.get_transaction_count(wallet_address)
        }
        
        # Set gas price if provided
        if gas_price:
            tx_params['gasPrice'] = gas_price
        elif hasattr(self.web3.eth, 'max_priority_fee'):
            # EIP-1559 transaction
            base_fee = self.web3.eth.get_block('latest')['baseFeePerGas']
            priority_fee = self.web3.eth.max_priority_fee
            tx_params['maxFeePerGas'] = base_fee + priority_fee
            tx_params['maxPriorityFeePerGas'] = priority_fee
        else:
            # Legacy transaction
            tx_params['gasPrice'] = self.web3.eth.gas_price
        
        # Check if buying with native token
        if base_token_address.lower() == self.native_token_address.lower():
            # Buy with ETH
            tx_params['value'] = amount_in
            
            # Prepare transaction
            tx = router_contract.functions.swapExactETHForTokens(
                estimation["min_amount_out"],
                estimation["path"],
                wallet_address,
                deadline
            ).build_transaction(tx_params)
        else:
            # Buy with ERC20 token
            # Prepare transaction
            tx = router_contract.functions.swapExactTokensForTokens(
                amount_in,
                estimation["min_amount_out"],
                estimation["path"],
                wallet_address,
                deadline
            ).build_transaction(tx_params)
        
        # Estimate gas
        try:
            gas_estimate = self.web3.eth.estimate_gas(tx)
            tx['gas'] = gas_estimate
        except Exception as e:
            logger.error(f"Gas estimation failed: {e}")
            # Use default gas limit
            tx['gas'] = 250000
        
        return {
            "transaction": tx,
            "estimation": estimation,
            "router_address": router_address,
            "deadline": deadline,
            "gas": tx['gas']
        }
    
    def prepare_sell_transaction(
        self,
        dex_id: str,
        token_address: str,
        amount_in: int,
        wallet_address: str,
        slippage: float = 1.0,
        base_token_address: str = None,
        gas_price: Optional[int] = None,
        deadline_minutes: int = 20
    ) -> Dict[str, Any]:
        """Prepare a transaction to sell a token

        Args:
            dex_id: DEX identifier (e.g., 'uniswap_v2')
            token_address: Token to sell
            amount_in: Input amount in wei
            wallet_address: Wallet address
            slippage: Slippage percentage
            base_token_address: Base token address (default is native token)
            gas_price: Gas price in wei (optional)
            deadline_minutes: Transaction deadline in minutes

        Returns:
            Dictionary with transaction details
        """
        # Use native token if base token not specified
        if not base_token_address:
            base_token_address = self.native_token_address
        
        # Get sell estimation
        estimation = self.estimate_sell(dex_id, token_address, amount_in, slippage, base_token_address)
        
        if "error" in estimation:
            return estimation
        
        # Get router address and ABI
        router_address = self.get_router_address(dex_id)
        router_abi = UNISWAP_V2_ROUTER_ABI
        
        # Create router contract
        router_contract = self.web3.eth.contract(
            address=router_address,
            abi=router_abi
        )
        
        # Set deadline
        deadline = self.web3.eth.get_block('latest')['timestamp'] + (deadline_minutes * 60)
        
        # Prepare transaction parameters
        tx_params = {
            'from': wallet_address,
            'nonce': self.web3.eth.get_transaction_count(wallet_address)
        }
        
        # Set gas price if provided
        if gas_price:
            tx_params['gasPrice'] = gas_price
        elif hasattr(self.web3.eth, 'max_priority_fee'):
            # EIP-1559 transaction
            base_fee = self.web3.eth.get_block('latest')['baseFeePerGas']
            priority_fee = self.web3.eth.max_priority_fee
            tx_params['maxFeePerGas'] = base_fee + priority_fee
            tx_params['maxPriorityFeePerGas'] = priority_fee
        else:
            # Legacy transaction
            tx_params['gasPrice'] = self.web3.eth.gas_price
        
        # Check if selling to native token
        if base_token_address.lower() == self.native_token_address.lower():
            # Sell for ETH
            tx = router_contract.functions.swapExactTokensForETH(
                amount_in,
                estimation["min_amount_out"],
                estimation["path"],
                wallet_address,
                deadline
            ).build_transaction(tx_params)
        else:
            # Sell for ERC20 token
            tx = router_contract.functions.swapExactTokensForTokens(
                amount_in,
                estimation["min_amount_out"],
                estimation["path"],
                wallet_address,
                deadline
            ).build_transaction(tx_params)
        
        # Estimate gas
        try:
            gas_estimate = self.web3.eth.estimate_gas(tx)
            tx['gas'] = gas_estimate
        except Exception as e:
            logger.error(f"Gas estimation failed: {e}")
            # Use default gas limit
            tx['gas'] = 250000
        
        return {
            "transaction": tx,
            "estimation": estimation,
            "router_address": router_address,
            "deadline": deadline,
            "gas": tx['gas']
        }

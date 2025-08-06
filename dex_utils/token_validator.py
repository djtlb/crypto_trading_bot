"""
Token Validator Module
=====================

Validates tokens for security issues and potential honeypots.
"""

from web3 import Web3
import logging
from typing import Dict, Any, Optional
from .dex_connector import DexConnector, ERC20_ABI

logger = logging.getLogger("TokenValidator")

class TokenValidator:
    """Validates tokens for security issues and potential honeypots"""
    
    def __init__(self, web3: Web3, chain_id: int):
        """Initialize the token validator

        Args:
            web3: Web3 instance
            chain_id: Chain ID
        """
        self.web3 = web3
        self.chain_id = chain_id
        self.dex_connector = DexConnector(web3, chain_id)
    
    def validate_token(self, token_address: str) -> Dict[str, Any]:
        """Validate a token for security issues

        Args:
            token_address: Token contract address

        Returns:
            Dictionary with validation results
        """
        # Validate address format
        if not Web3.is_address(token_address):
            return {
                "is_valid": False,
                "is_honeypot": False,
                "can_buy": False,
                "can_sell": False,
                "details": "Invalid token address format"
            }
        
        token_address = Web3.to_checksum_address(token_address)
        
        # Check if contract exists
        code = self.web3.eth.get_code(token_address)
        if len(code) <= 2:  # '0x' or empty
            return {
                "is_valid": False,
                "is_honeypot": False,
                "can_buy": False,
                "can_sell": False,
                "details": "No contract code at address"
            }
        
        try:
            # Get token information
            token_info = self.dex_connector.get_token_info(token_address)
            
            # Test ERC20 functions
            token_contract = self.web3.eth.contract(
                address=token_address,
                abi=ERC20_ABI
            )
            
            # Test basic functions
            try:
                name = token_contract.functions.name().call()
                symbol = token_contract.functions.symbol().call()
                decimals = token_contract.functions.decimals().call()
                total_supply = token_contract.functions.balanceOf(token_address).call()
            except Exception as e:
                logger.warning(f"Token {token_address} failed basic ERC20 function tests: {e}")
                return {
                    "is_valid": False,
                    "is_honeypot": True,
                    "can_buy": False,
                    "can_sell": False,
                    "details": f"Failed basic ERC20 function tests: {str(e)}"
                }
            
            # Check buying/selling with small amounts
            is_honeypot, can_buy, can_sell, message = self._check_buy_sell(token_address)
            
            # Check if token has transfer restrictions
            has_transfer_restrictions = self._check_transfer_restrictions(token_address)
            
            # Build result
            result = {
                "is_valid": True,
                "is_honeypot": is_honeypot,
                "can_buy": can_buy,
                "can_sell": can_sell,
                "has_transfer_restrictions": has_transfer_restrictions,
                "details": message,
                "token_info": token_info
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating token {token_address}: {e}")
            return {
                "is_valid": False,
                "is_honeypot": True,
                "can_buy": False,
                "can_sell": False,
                "details": f"Validation failed: {str(e)}"
            }
    
    def _check_buy_sell(self, token_address: str) -> tuple:
        """Check if token can be bought and sold

        Args:
            token_address: Token contract address

        Returns:
            Tuple (is_honeypot, can_buy, can_sell, message)
        """
        # Determine which DEX to use for this chain
        dex_id = None
        if self.chain_id == 1:  # Ethereum
            dex_id = "uniswap_v2"
        elif self.chain_id == 56:  # BSC
            dex_id = "pancakeswap_v2"
        elif self.chain_id == 137:  # Polygon
            dex_id = "quickswap"
        elif self.chain_id == 42161:  # Arbitrum
            dex_id = "uniswap_v3"
        
        if not dex_id:
            return True, False, False, f"Chain ID {self.chain_id} not supported for honeypot check"
        
        # Get DEX router
        try:
            router_address = self.dex_connector.get_router_address(dex_id)
        except ValueError:
            return False, False, False, f"DEX {dex_id} not supported on chain {self.chain_id}"
        
        # Try to estimate buy
        try:
            native_token = self.dex_connector.native_token_address
            small_amount = 10 ** 16  # 0.01 ETH/BNB/etc
            buy_estimate = self.dex_connector.estimate_buy(
                dex_id,
                token_address,
                small_amount,
                slippage=5.0
            )
            
            if "error" in buy_estimate:
                return True, False, False, f"Cannot buy token: {buy_estimate.get('error')}"
                
            can_buy = True
        except Exception as e:
            logger.warning(f"Cannot estimate buy for {token_address}: {e}")
            can_buy = False
        
        # Try to estimate sell
        try:
            # Use a very small amount for testing
            token_info = self.dex_connector.get_token_info(token_address)
            small_token_amount = 10 ** token_info["decimals"] // 1000  # 0.001 tokens
            
            sell_estimate = self.dex_connector.estimate_sell(
                dex_id,
                token_address,
                small_token_amount,
                slippage=5.0
            )
            
            if "error" in sell_estimate:
                return True, can_buy, False, f"Cannot sell token: {sell_estimate.get('error')}"
                
            can_sell = True
        except Exception as e:
            logger.warning(f"Cannot estimate sell for {token_address}: {e}")
            can_sell = False
        
        # Determine if it's a honeypot
        is_honeypot = not can_buy or not can_sell
        
        message = "Token passed buy/sell tests"
        if not can_buy and not can_sell:
            message = "Token cannot be bought or sold"
        elif not can_buy:
            message = "Token cannot be bought"
        elif not can_sell:
            message = "Token cannot be sold (potential honeypot)"
        
        return is_honeypot, can_buy, can_sell, message
    
    def _check_transfer_restrictions(self, token_address: str) -> bool:
        """Check if token has transfer restrictions

        Args:
            token_address: Token contract address

        Returns:
            True if token has transfer restrictions
        """
        # This is a simplified check. A more comprehensive check would involve:
        # 1. Checking for blacklisted addresses
        # 2. Checking for transfer fees
        # 3. Checking for max transaction limits
        
        # These would require deeper contract analysis or test transfers
        
        # For now, just return False (no restrictions detected)
        return False

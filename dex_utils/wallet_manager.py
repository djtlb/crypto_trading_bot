"""
Wallet Manager Module
====================

Securely manages wallet connections and operations for the DEX bot.
"""

from web3 import Web3
from eth_account import Account
import os
import json
import logging
from typing import Optional, Dict, Any, Tuple
from cryptography.fernet import Fernet

logger = logging.getLogger("WalletManager")

class WalletManager:
    """Manages wallet interactions including secure private key handling"""
    
    def __init__(
        self, 
        private_key: Optional[str] = None, 
        address: Optional[str] = None,
        fernet: Optional[Fernet] = None
    ):
        """Initialize wallet manager with either private key or address

        Args:
            private_key: Ethereum private key (without 0x prefix)
            address: Ethereum address for read-only mode
            fernet: Fernet encryption instance for secure key storage
        """
        self.address = None
        self.private_key = None
        self._encrypted_key = None
        self.is_read_only = True
        
        if private_key and private_key.startswith("0x"):
            private_key = private_key[2:]
            
        if private_key:
            # Initialize with private key
            try:
                account = Account.from_key(private_key)
                self.address = account.address
                
                # Securely store private key if encryption is available
                if fernet:
                    self._encrypted_key = fernet.encrypt(private_key.encode()).decode()
                else:
                    # Not recommended, but store in memory if no encryption
                    self.private_key = private_key
                    
                self.is_read_only = False
                logger.info(f"Initialized wallet with private key for {self.address}")
                
            except Exception as e:
                logger.error(f"Failed to initialize wallet with private key: {e}")
                raise ValueError(f"Invalid private key: {e}")
                
        elif address:
            # Read-only mode
            if Web3.is_address(address):
                self.address = Web3.to_checksum_address(address)
                self.is_read_only = True
                logger.info(f"Initialized wallet in read-only mode for {self.address}")
            else:
                raise ValueError("Invalid Ethereum address")
        else:
            raise ValueError("Either private key or address must be provided")
    
    def get_private_key(self, fernet: Optional[Fernet] = None) -> str:
        """Get private key, decrypting if necessary

        Args:
            fernet: Fernet encryption instance for decryption

        Returns:
            The private key

        Raises:
            ValueError: If wallet is in read-only mode or decryption fails
        """
        if self.is_read_only:
            raise ValueError("Cannot get private key in read-only mode")
            
        if self.private_key:
            return self.private_key
            
        if self._encrypted_key and fernet:
            try:
                return fernet.decrypt(self._encrypted_key.encode()).decode()
            except Exception as e:
                logger.error(f"Failed to decrypt private key: {e}")
                raise ValueError(f"Failed to decrypt private key: {e}")
        
        raise ValueError("Private key not available")
    
    def sign_transaction(
        self, 
        tx_params: Dict[str, Any], 
        web3: Web3,
        fernet: Optional[Fernet] = None
    ) -> str:
        """Sign a transaction

        Args:
            tx_params: Transaction parameters
            web3: Web3 instance
            fernet: Fernet encryption instance for decryption

        Returns:
            Signed transaction hash

        Raises:
            ValueError: If wallet is in read-only mode
        """
        if self.is_read_only:
            raise ValueError("Cannot sign transaction in read-only mode")
            
        private_key = self.get_private_key(fernet)
        
        # Get nonce if not provided
        if 'nonce' not in tx_params:
            tx_params['nonce'] = web3.eth.get_transaction_count(self.address)
        
        # Sign transaction
        signed_tx = web3.eth.account.sign_transaction(tx_params, private_key)
        
        return signed_tx
    
    def send_transaction(
        self, 
        tx_params: Dict[str, Any], 
        web3: Web3,
        fernet: Optional[Fernet] = None
    ) -> str:
        """Sign and send a transaction

        Args:
            tx_params: Transaction parameters
            web3: Web3 instance
            fernet: Fernet encryption instance for decryption

        Returns:
            Transaction hash

        Raises:
            ValueError: If wallet is in read-only mode
        """
        if self.is_read_only:
            raise ValueError("Cannot send transaction in read-only mode")
            
        signed_tx = self.sign_transaction(tx_params, web3, fernet)
        
        # Send transaction
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        logger.info(f"Transaction sent: {tx_hash.hex()}")
        return tx_hash.hex()
    
    def approve_token(
        self, 
        token_address: str, 
        spender_address: str, 
        amount: int,
        web3: Web3,
        fernet: Optional[Fernet] = None,
        gas_price: Optional[int] = None,
        gas_limit: Optional[int] = None
    ) -> str:
        """Approve a token for spending by a contract

        Args:
            token_address: Token contract address
            spender_address: Address of the contract to approve
            amount: Amount to approve (in wei)
            web3: Web3 instance
            fernet: Fernet encryption instance for decryption
            gas_price: Gas price in wei (optional)
            gas_limit: Gas limit (optional)

        Returns:
            Transaction hash

        Raises:
            ValueError: If wallet is in read-only mode
        """
        if self.is_read_only:
            raise ValueError("Cannot approve token in read-only mode")
            
        # ERC20 approve function ABI
        abi = [{
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
        }]
        
        token_contract = web3.eth.contract(address=token_address, abi=abi)
        
        # Prepare transaction
        tx_params = {
            'from': self.address,
            'nonce': web3.eth.get_transaction_count(self.address)
        }
        
        # Set gas price if provided
        if gas_price:
            tx_params['gasPrice'] = gas_price
        elif hasattr(web3.eth, 'max_priority_fee'):
            # EIP-1559 transaction
            base_fee = web3.eth.get_block('latest')['baseFeePerGas']
            priority_fee = web3.eth.max_priority_fee
            tx_params['maxFeePerGas'] = base_fee + priority_fee
            tx_params['maxPriorityFeePerGas'] = priority_fee
        else:
            # Legacy transaction
            tx_params['gasPrice'] = web3.eth.gas_price
        
        # Build the transaction
        tx = token_contract.functions.approve(spender_address, amount).build_transaction(tx_params)
        
        # Set gas limit if provided
        if gas_limit:
            tx['gas'] = gas_limit
        
        # Sign and send transaction
        return self.send_transaction(tx, web3, fernet)
    
    def is_token_approved(
        self, 
        token_address: str, 
        spender_address: str,
        amount: int,
        web3: Web3
    ) -> bool:
        """Check if a token is approved for spending

        Args:
            token_address: Token contract address
            spender_address: Address of the contract to check
            amount: Amount to check approval for
            web3: Web3 instance

        Returns:
            True if token is approved for at least the requested amount
        """
        # ERC20 allowance function ABI
        abi = [{
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
        }]
        
        token_contract = web3.eth.contract(address=token_address, abi=abi)
        
        # Check allowance
        allowance = token_contract.functions.allowance(self.address, spender_address).call()
        
        return allowance >= amount

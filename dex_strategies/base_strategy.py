"""
Base Strategy Module
==================

Base class for all trading strategies.
"""

from web3 import Web3
import time
import logging
import threading
from typing import Dict, Any, Optional
from dex_utils.dex_connector import DexConnector
from dex_utils.wallet_manager import WalletManager
from cryptography.fernet import Fernet

logger = logging.getLogger("BaseStrategy")

class BaseStrategy:
    """Base class for all trading strategies"""
    
    def __init__(
        self,
        wallet_manager: WalletManager,
        web3: Web3,
        chain_id: int,
        dex_id: str,
        token_address: str,
        base_token_address: Optional[str] = None,
        amount: float = 0.01,
        slippage: float = 1.0,
        gas_price: str = "auto",
        gas_limit: str = "auto",
        profit_target: float = 5.0,
        stop_loss: float = 2.0,
        trailing_stop: bool = False
    ):
        """Initialize the strategy

        Args:
            wallet_manager: Wallet manager instance
            web3: Web3 instance
            chain_id: Chain ID
            dex_id: DEX identifier (e.g., 'uniswap_v2')
            token_address: Token to trade
            base_token_address: Base token address (default is native token)
            amount: Amount to trade in base token units
            slippage: Slippage percentage
            gas_price: Gas price in wei or 'auto'
            gas_limit: Gas limit or 'auto'
            profit_target: Profit target percentage
            stop_loss: Stop loss percentage
            trailing_stop: Whether to use trailing stop
        """
        self.wallet_manager = wallet_manager
        self.web3 = web3
        self.chain_id = chain_id
        self.dex_id = dex_id
        self.token_address = Web3.to_checksum_address(token_address)
        
        # Set base token (default to native token if not specified)
        if base_token_address:
            self.base_token_address = Web3.to_checksum_address(base_token_address)
        else:
            # Use native token address
            self.base_token_address = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
        
        # Trading parameters
        self.amount = amount
        self.slippage = slippage
        self.gas_price = gas_price
        self.gas_limit = gas_limit
        self.profit_target = profit_target
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop
        
        # Strategy state
        self.running = False
        self.trade_state = "idle"  # idle, buying, bought, selling, sold, error
        self.position = None
        self.entry_price = None
        self.current_price = None
        self.highest_price = None
        self.lowest_price = None
        self.monitor_thread = None
        self.fernet = None
        
        # Performance metrics
        self.trades = []
        self.trade_history = []
        
        # Initialize DEX connector
        self.dex_connector = DexConnector(web3, chain_id)
    
    def set_encryption(self, fernet: Fernet):
        """Set encryption for secure wallet operations

        Args:
            fernet: Fernet encryption instance
        """
        self.fernet = fernet
    
    def start(self):
        """Start the strategy"""
        if self.running:
            logger.warning("Strategy already running")
            return
        
        self.running = True
        self.trade_state = "idle"
        
        # Start monitor thread if needed
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self.monitor_thread.start()
        
        logger.info(f"Strategy started for {self.token_address}")
    
    def stop(self):
        """Stop the strategy"""
        self.running = False
        
        # Wait for monitor thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        logger.info(f"Strategy stopped for {self.token_address}")
    
    def execute_strategy(self):
        """Execute the strategy logic

        Returns:
            Dictionary with execution results
        """
        # This method should be implemented by subclasses
        raise NotImplementedError("Subclasses must implement execute_strategy method")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get strategy performance metrics

        Returns:
            Dictionary with performance metrics
        """
        total_trades = len(self.trades)
        profitable_trades = sum(1 for trade in self.trades if trade["profit_pct"] > 0)
        
        if total_trades > 0:
            win_rate = (profitable_trades / total_trades) * 100
            avg_profit = sum(trade["profit_pct"] for trade in self.trades) / total_trades
        else:
            win_rate = 0
            avg_profit = 0
        
        return {
            "total_trades": total_trades,
            "profitable_trades": profitable_trades,
            "win_rate": win_rate,
            "avg_profit_pct": avg_profit,
            "current_position": self.position,
            "trade_state": self.trade_state,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "profit_target": self.profit_target,
            "stop_loss": self.stop_loss
        }
    
    def buy(self) -> Dict[str, Any]:
        """Execute a buy order

        Returns:
            Dictionary with buy results
        """
        if self.wallet_manager.is_read_only:
            return {
                "success": False,
                "message": "Cannot trade with read-only wallet",
                "action": "error"
            }
        
        if self.trade_state == "buying" or self.trade_state == "bought":
            return {
                "success": False,
                "message": f"Already in position. Current state: {self.trade_state}",
                "action": "none"
            }
        
        try:
            # Update state
            self.trade_state = "buying"
            
            # Convert amount to wei
            token_info = self.dex_connector.get_token_info(self.base_token_address)
            amount_wei = int(self.amount * (10 ** token_info["decimals"]))
            
            # Check if we have enough balance
            balance = self.dex_connector.get_token_balance(
                self.base_token_address,
                self.wallet_manager.address
            )
            
            if int(balance["balance_wei"]) < amount_wei:
                self.trade_state = "error"
                return {
                    "success": False,
                    "message": f"Insufficient balance. Have: {balance['balance']}, Need: {self.amount}",
                    "action": "error"
                }
            
            # Prepare buy transaction
            tx_data = self.dex_connector.prepare_buy_transaction(
                self.dex_id,
                self.token_address,
                amount_wei,
                self.wallet_manager.address,
                self.slippage,
                self.base_token_address
            )
            
            if "error" in tx_data:
                self.trade_state = "error"
                return {
                    "success": False,
                    "message": f"Failed to prepare buy transaction: {tx_data.get('error')}",
                    "action": "error"
                }
            
            # Check if we need approval for ERC20 tokens
            if self.base_token_address != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
                # Check if token is approved
                is_approved = self.wallet_manager.is_token_approved(
                    self.base_token_address,
                    tx_data["router_address"],
                    amount_wei,
                    self.web3
                )
                
                if not is_approved:
                    # Approve token
                    logger.info(f"Approving {self.base_token_address} for trading")
                    approve_tx = self.wallet_manager.approve_token(
                        self.base_token_address,
                        tx_data["router_address"],
                        2 ** 256 - 1,  # Unlimited approval
                        self.web3,
                        self.fernet
                    )
                    
                    # Wait for approval to be mined
                    logger.info(f"Waiting for approval transaction to be mined: {approve_tx}")
                    self.web3.eth.wait_for_transaction_receipt(approve_tx)
            
            # Send buy transaction
            tx_hash = self.wallet_manager.send_transaction(
                tx_data["transaction"],
                self.web3,
                self.fernet
            )
            
            logger.info(f"Buy transaction sent: {tx_hash}")
            
            # Wait for transaction to be mined
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                # Transaction successful
                self.trade_state = "bought"
                self.position = {
                    "token_address": self.token_address,
                    "amount_in": tx_data["estimation"]["amount_in_units"],
                    "amount_out": tx_data["estimation"]["amount_out_units"],
                    "tx_hash": tx_hash,
                    "timestamp": int(time.time())
                }
                
                self.entry_price = tx_data["estimation"]["amount_in_units"] / tx_data["estimation"]["amount_out_units"]
                self.current_price = self.entry_price
                self.highest_price = self.entry_price
                
                return {
                    "success": True,
                    "message": f"Buy successful: {tx_hash}",
                    "action": "buy",
                    "tx_hash": tx_hash,
                    "amount_in": tx_data["estimation"]["amount_in_units"],
                    "amount_out": tx_data["estimation"]["amount_out_units"],
                    "entry_price": self.entry_price
                }
            else:
                # Transaction failed
                self.trade_state = "error"
                return {
                    "success": False,
                    "message": f"Buy transaction failed: {tx_hash}",
                    "action": "error",
                    "tx_hash": tx_hash
                }
                
        except Exception as e:
            logger.error(f"Buy error: {e}")
            self.trade_state = "error"
            return {
                "success": False,
                "message": f"Buy error: {str(e)}",
                "action": "error"
            }
    
    def sell(self) -> Dict[str, Any]:
        """Execute a sell order

        Returns:
            Dictionary with sell results
        """
        if self.wallet_manager.is_read_only:
            return {
                "success": False,
                "message": "Cannot trade with read-only wallet",
                "action": "error"
            }
        
        if self.trade_state != "bought":
            return {
                "success": False,
                "message": f"No position to sell. Current state: {self.trade_state}",
                "action": "none"
            }
        
        try:
            # Update state
            self.trade_state = "selling"
            
            # Get token balance
            balance = self.dex_connector.get_token_balance(
                self.token_address,
                self.wallet_manager.address
            )
            
            if float(balance["balance"]) <= 0:
                self.trade_state = "error"
                return {
                    "success": False,
                    "message": f"No tokens to sell. Balance: {balance['balance']}",
                    "action": "error"
                }
            
            # Prepare sell transaction
            amount_wei = int(balance["balance_wei"])
            
            tx_data = self.dex_connector.prepare_sell_transaction(
                self.dex_id,
                self.token_address,
                amount_wei,
                self.wallet_manager.address,
                self.slippage,
                self.base_token_address
            )
            
            if "error" in tx_data:
                self.trade_state = "error"
                return {
                    "success": False,
                    "message": f"Failed to prepare sell transaction: {tx_data.get('error')}",
                    "action": "error"
                }
            
            # Check if we need approval
            is_approved = self.wallet_manager.is_token_approved(
                self.token_address,
                tx_data["router_address"],
                amount_wei,
                self.web3
            )
            
            if not is_approved:
                # Approve token
                logger.info(f"Approving {self.token_address} for trading")
                approve_tx = self.wallet_manager.approve_token(
                    self.token_address,
                    tx_data["router_address"],
                    2 ** 256 - 1,  # Unlimited approval
                    self.web3,
                    self.fernet
                )
                
                # Wait for approval to be mined
                logger.info(f"Waiting for approval transaction to be mined: {approve_tx}")
                self.web3.eth.wait_for_transaction_receipt(approve_tx)
            
            # Send sell transaction
            tx_hash = self.wallet_manager.send_transaction(
                tx_data["transaction"],
                self.web3,
                self.fernet
            )
            
            logger.info(f"Sell transaction sent: {tx_hash}")
            
            # Wait for transaction to be mined
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                # Transaction successful
                self.trade_state = "sold"
                
                # Calculate profit/loss
                exit_price = tx_data["estimation"]["amount_out_units"] / tx_data["estimation"]["amount_in_units"]
                profit_pct = ((exit_price / self.entry_price) - 1) * 100
                
                # Record trade
                trade = {
                    "entry_price": self.entry_price,
                    "exit_price": exit_price,
                    "profit_pct": profit_pct,
                    "amount_in": self.position["amount_in"],
                    "amount_out": tx_data["estimation"]["amount_out_units"],
                    "token_address": self.token_address,
                    "buy_tx": self.position["tx_hash"],
                    "sell_tx": tx_hash,
                    "timestamp": int(time.time())
                }
                
                self.trades.append(trade)
                self.trade_history.append(trade)
                
                # Reset position
                self.position = None
                self.entry_price = None
                self.current_price = None
                self.highest_price = None
                
                return {
                    "success": True,
                    "message": f"Sell successful: {tx_hash}",
                    "action": "sell",
                    "tx_hash": tx_hash,
                    "profit_pct": profit_pct,
                    "profit_usd": self.position["amount_in"] * (profit_pct / 100) if self.position else 0
                }
            else:
                # Transaction failed
                self.trade_state = "error"
                return {
                    "success": False,
                    "message": f"Sell transaction failed: {tx_hash}",
                    "action": "error",
                    "tx_hash": tx_hash
                }
                
        except Exception as e:
            logger.error(f"Sell error: {e}")
            self.trade_state = "error"
            return {
                "success": False,
                "message": f"Sell error: {str(e)}",
                "action": "error"
            }
    
    def update_price(self) -> float:
        """Update current token price

        Returns:
            Current price in base token units
        """
        try:
            # Get smallest amount of token (1 unit)
            token_info = self.dex_connector.get_token_info(self.token_address)
            one_token = 10 ** token_info["decimals"]
            
            # Get price
            price_data = self.dex_connector.get_price_impact(
                self.dex_id,
                self.token_address,
                self.base_token_address,
                one_token
            )
            
            if "error" in price_data:
                logger.warning(f"Error updating price: {price_data.get('error')}")
                return self.current_price
            
            self.current_price = price_data["amount_out"] / one_token
            
            # Update highest/lowest price
            if self.highest_price is None or self.current_price > self.highest_price:
                self.highest_price = self.current_price
                
            if self.lowest_price is None or self.current_price < self.lowest_price:
                self.lowest_price = self.current_price
            
            return self.current_price
            
        except Exception as e:
            logger.error(f"Error updating price: {e}")
            return self.current_price
    
    def check_exit_conditions(self) -> bool:
        """Check if we should exit the position

        Returns:
            True if we should exit, False otherwise
        """
        if self.trade_state != "bought" or not self.position or not self.entry_price or not self.current_price:
            return False
        
        # Calculate current profit/loss
        profit_pct = ((self.current_price / self.entry_price) - 1) * 100
        
        # Check profit target
        if profit_pct >= self.profit_target:
            logger.info(f"Profit target reached: {profit_pct:.2f}% >= {self.profit_target:.2f}%")
            return True
        
        # Check stop loss
        if profit_pct <= -self.stop_loss:
            logger.info(f"Stop loss triggered: {profit_pct:.2f}% <= -{self.stop_loss:.2f}%")
            return True
        
        # Check trailing stop
        if self.trailing_stop and self.highest_price:
            max_profit_pct = ((self.highest_price / self.entry_price) - 1) * 100
            drawdown = max_profit_pct - profit_pct
            
            if max_profit_pct > self.profit_target / 2:
                # If we've reached 50% of profit target, use trailing stop
                trailing_stop_trigger = max_profit_pct / 3  # Trail by 1/3 of max profit
                
                if drawdown >= trailing_stop_trigger:
                    logger.info(f"Trailing stop triggered: Drawdown {drawdown:.2f}% >= {trailing_stop_trigger:.2f}%")
                    return True
        
        return False
    
    def _monitor_loop(self):
        """Monitor loop for price updates and exit conditions"""
        while self.running:
            try:
                # Update price
                if self.trade_state == "bought" and self.position:
                    self.update_price()
                    
                    # Check exit conditions
                    if self.check_exit_conditions():
                        logger.info("Exit conditions met, selling position")
                        self.sell()
                
                # Sleep
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(30)  # Wait longer on error

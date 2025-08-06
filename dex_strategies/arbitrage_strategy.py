"""
DEX Arbitrage Strategy
=====================

A strategy for exploiting price differences between different DEXes.
"""

import time
import logging
from web3 import Web3
from dex_strategies.base_strategy import BaseStrategy
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger("ArbitrageStrategy")

class ArbitrageStrategy(BaseStrategy):
    """Strategy for arbitrage between different DEXes."""
    
    def __init__(
        self,
        wallet_manager,
        web3: Web3,
        chain_id: int,
        source_dex_id: str,
        target_dex_id: str,
        token_address: str,
        base_token_address: Optional[str] = None,
        amount: float = 0.1,
        slippage: float = 0.5,
        gas_price: str = "auto",
        gas_limit: str = "auto",
        min_profit_threshold: float = 1.0,
        check_interval: int = 30,
        max_concurrent_arbs: int = 1,
        retry_delay: int = 60
    ):
        """Initialize the arbitrage strategy

        Args:
            wallet_manager: Wallet manager instance
            web3: Web3 instance
            chain_id: Chain ID
            source_dex_id: Source DEX identifier (e.g., 'uniswap_v2')
            target_dex_id: Target DEX identifier (e.g., 'sushiswap')
            token_address: Token to arbitrage
            base_token_address: Base token address (default is native token)
            amount: Amount to trade in base token units
            slippage: Slippage percentage
            gas_price: Gas price in wei or 'auto'
            gas_limit: Gas limit or 'auto'
            min_profit_threshold: Minimum profit percentage to execute arbitrage
            check_interval: Seconds between price checks
            max_concurrent_arbs: Maximum number of concurrent arbitrage operations
            retry_delay: Delay in seconds before retrying after failure
        """
        # Initialize with source DEX first
        super().__init__(
            wallet_manager=wallet_manager,
            web3=web3,
            chain_id=chain_id,
            dex_id=source_dex_id,
            token_address=token_address,
            base_token_address=base_token_address,
            amount=amount,
            slippage=slippage,
            gas_price=gas_price,
            gas_limit=gas_limit,
            profit_target=min_profit_threshold,
            stop_loss=100.0,  # Large stop loss as we're not holding
            trailing_stop=False
        )
        
        # Arbitrage-specific parameters
        self.source_dex_id = source_dex_id
        self.target_dex_id = target_dex_id
        self.min_profit_threshold = min_profit_threshold
        self.check_interval = check_interval
        self.max_concurrent_arbs = max_concurrent_arbs
        self.retry_delay = retry_delay
        
        # Arbitrage state
        self.last_check_time = 0
        self.active_arbitrages = 0
        self.arbitrage_history = []
        self.last_failure_time = 0
    
    def execute_strategy(self) -> Dict[str, Any]:
        """Execute the arbitrage strategy

        Returns:
            Dictionary with execution results
        """
        current_time = int(time.time())
        
        # Check if we need to wait after a failure
        if self.last_failure_time and current_time - self.last_failure_time < self.retry_delay:
            return {
                "success": True,
                "action": "wait",
                "message": f"Waiting for retry delay ({self.retry_delay}s)",
                "wait_time_remaining": self.retry_delay - (current_time - self.last_failure_time)
            }
        
        # Check if we've reached the maximum concurrent arbitrages
        if self.active_arbitrages >= self.max_concurrent_arbs:
            return {
                "success": True,
                "action": "skip",
                "message": f"Maximum concurrent arbitrages reached ({self.max_concurrent_arbs})",
                "active_arbitrages": self.active_arbitrages
            }
        
        # Check if it's time to check prices
        if current_time - self.last_check_time < self.check_interval:
            return {
                "success": True,
                "action": "wait",
                "message": f"Waiting for next price check ({self.check_interval}s)",
                "wait_time_remaining": self.check_interval - (current_time - self.last_check_time)
            }
        
        # Update last check time
        self.last_check_time = current_time
        
        # Check for arbitrage opportunity
        arb_opportunity = self._check_arbitrage_opportunity()
        
        if not arb_opportunity["success"]:
            return {
                "success": False,
                "action": "error",
                "message": f"Error checking arbitrage opportunity: {arb_opportunity['message']}",
                "details": arb_opportunity
            }
        
        # If no profitable opportunity, wait for next check
        if not arb_opportunity["profitable"]:
            return {
                "success": True,
                "action": "wait",
                "message": f"No profitable arbitrage opportunity found. Current spread: {arb_opportunity['profit_pct']:.2f}%",
                "details": arb_opportunity
            }
        
        # Execute arbitrage
        self.active_arbitrages += 1
        arbitrage_result = self._execute_arbitrage(arb_opportunity)
        
        if not arbitrage_result["success"]:
            self.active_arbitrages -= 1
            self.last_failure_time = current_time
            return {
                "success": False,
                "action": "error",
                "message": f"Arbitrage execution failed: {arbitrage_result['message']}",
                "details": arbitrage_result
            }
        
        # Record successful arbitrage
        self.arbitrage_history.append({
            "timestamp": current_time,
            "source_dex": self.source_dex_id,
            "target_dex": self.target_dex_id,
            "token_address": self.token_address,
            "amount": self.amount,
            "profit_pct": arbitrage_result["profit_pct"],
            "profit_amount": arbitrage_result["profit_amount"],
            "gas_cost": arbitrage_result["gas_cost"],
            "net_profit": arbitrage_result["net_profit"],
            "buy_tx": arbitrage_result["buy_tx"],
            "sell_tx": arbitrage_result["sell_tx"]
        })
        
        self.active_arbitrages -= 1
        
        return {
            "success": True,
            "action": "arbitrage",
            "message": f"Arbitrage executed with {arbitrage_result['profit_pct']:.2f}% profit",
            "details": arbitrage_result
        }
    
    def _check_arbitrage_opportunity(self) -> Dict[str, Any]:
        """Check for arbitrage opportunity between DEXes

        Returns:
            Dictionary with arbitrage opportunity details
        """
        try:
            # Get token info
            token_info = self.dex_connector.get_token_info(self.token_address)
            base_token_info = self.dex_connector.get_token_info(self.base_token_address)
            
            # Convert amount to wei
            amount_wei = int(self.amount * (10 ** base_token_info["decimals"]))
            
            # Check buy price on source DEX
            source_buy_price = self.dex_connector.get_price_impact(
                self.source_dex_id,
                self.token_address,
                self.base_token_address,
                amount_wei,
                "buy"
            )
            
            if "error" in source_buy_price:
                return {
                    "success": False,
                    "message": f"Error getting source DEX buy price: {source_buy_price.get('error')}",
                    "profitable": False
                }
            
            # Calculate how many tokens we would get from source DEX
            tokens_received = source_buy_price["amount_out"]
            
            # Check sell price on target DEX
            target_sell_price = self.dex_connector.get_price_impact(
                self.target_dex_id,
                self.token_address,
                self.base_token_address,
                tokens_received,
                "sell"
            )
            
            if "error" in target_sell_price:
                return {
                    "success": False,
                    "message": f"Error getting target DEX sell price: {target_sell_price.get('error')}",
                    "profitable": False
                }
            
            # Calculate how much base token we would get back
            base_tokens_received = target_sell_price["amount_out"]
            
            # Calculate profit in base token units
            profit_amount_wei = base_tokens_received - amount_wei
            profit_amount = profit_amount_wei / (10 ** base_token_info["decimals"])
            
            # Calculate profit percentage
            profit_pct = (profit_amount / self.amount) * 100
            
            # Estimate gas cost for the arbitrage (two transactions)
            est_gas_cost = self._estimate_gas_cost()
            
            if not est_gas_cost["success"]:
                return {
                    "success": False,
                    "message": f"Error estimating gas cost: {est_gas_cost['error']}",
                    "profitable": False
                }
            
            # Calculate net profit after gas
            net_profit = profit_amount - est_gas_cost["total_gas_cost_base"]
            net_profit_pct = (net_profit / self.amount) * 100
            
            # Check if profitable after gas costs
            profitable = net_profit_pct >= self.min_profit_threshold
            
            return {
                "success": True,
                "profitable": profitable,
                "source_dex": self.source_dex_id,
                "target_dex": self.target_dex_id,
                "amount_in": self.amount,
                "amount_in_wei": amount_wei,
                "tokens_received": tokens_received / (10 ** token_info["decimals"]),
                "tokens_received_wei": tokens_received,
                "base_tokens_returned": base_tokens_received / (10 ** base_token_info["decimals"]),
                "base_tokens_returned_wei": base_tokens_received,
                "profit_amount": profit_amount,
                "profit_amount_wei": profit_amount_wei,
                "profit_pct": profit_pct,
                "estimated_gas_cost": est_gas_cost,
                "net_profit": net_profit,
                "net_profit_pct": net_profit_pct,
                "min_profit_threshold": self.min_profit_threshold
            }
            
        except Exception as e:
            logger.error(f"Error checking arbitrage opportunity: {e}")
            return {
                "success": False,
                "message": f"Error checking arbitrage opportunity: {str(e)}",
                "profitable": False
            }
    
    def _execute_arbitrage(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an arbitrage opportunity

        Args:
            opportunity: Arbitrage opportunity details

        Returns:
            Dictionary with arbitrage execution results
        """
        try:
            start_time = int(time.time())
            
            # Buy tokens on source DEX
            logger.info(f"Executing arbitrage: Buying on {self.source_dex_id}, selling on {self.target_dex_id}")
            
            # Prepare buy transaction on source DEX
            buy_tx_data = self.dex_connector.prepare_buy_transaction(
                self.source_dex_id,
                self.token_address,
                opportunity["amount_in_wei"],
                self.wallet_manager.address,
                self.slippage,
                self.base_token_address
            )
            
            if "error" in buy_tx_data:
                return {
                    "success": False,
                    "message": f"Failed to prepare buy transaction: {buy_tx_data.get('error')}",
                    "stage": "buy_preparation"
                }
            
            # Check if we need approval for ERC20 tokens
            if self.base_token_address != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
                # Check if token is approved
                is_approved = self.wallet_manager.is_token_approved(
                    self.base_token_address,
                    buy_tx_data["router_address"],
                    opportunity["amount_in_wei"],
                    self.web3
                )
                
                if not is_approved:
                    # Approve token
                    logger.info(f"Approving {self.base_token_address} for trading on {self.source_dex_id}")
                    approve_tx = self.wallet_manager.approve_token(
                        self.base_token_address,
                        buy_tx_data["router_address"],
                        2 ** 256 - 1,  # Unlimited approval
                        self.web3,
                        self.fernet
                    )
                    
                    # Wait for approval to be mined
                    logger.info(f"Waiting for approval transaction to be mined: {approve_tx}")
                    self.web3.eth.wait_for_transaction_receipt(approve_tx)
            
            # Send buy transaction
            buy_tx_hash = self.wallet_manager.send_transaction(
                buy_tx_data["transaction"],
                self.web3,
                self.fernet
            )
            
            logger.info(f"Buy transaction sent: {buy_tx_hash}")
            
            # Wait for transaction to be mined
            buy_receipt = self.web3.eth.wait_for_transaction_receipt(buy_tx_hash)
            
            if buy_receipt["status"] != 1:
                return {
                    "success": False,
                    "message": f"Buy transaction failed: {buy_tx_hash}",
                    "stage": "buy_execution",
                    "tx_hash": buy_tx_hash
                }
            
            # Get actual tokens received
            token_balance = self.dex_connector.get_token_balance(
                self.token_address,
                self.wallet_manager.address
            )
            
            tokens_received_wei = int(token_balance["balance_wei"])
            
            # Prepare sell transaction on target DEX
            sell_tx_data = self.dex_connector.prepare_sell_transaction(
                self.target_dex_id,
                self.token_address,
                tokens_received_wei,
                self.wallet_manager.address,
                self.slippage,
                self.base_token_address
            )
            
            if "error" in sell_tx_data:
                return {
                    "success": False,
                    "message": f"Failed to prepare sell transaction: {sell_tx_data.get('error')}",
                    "stage": "sell_preparation",
                    "buy_tx": buy_tx_hash
                }
            
            # Check if we need approval for the target DEX
            is_approved = self.wallet_manager.is_token_approved(
                self.token_address,
                sell_tx_data["router_address"],
                tokens_received_wei,
                self.web3
            )
            
            if not is_approved:
                # Approve token
                logger.info(f"Approving {self.token_address} for trading on {self.target_dex_id}")
                approve_tx = self.wallet_manager.approve_token(
                    self.token_address,
                    sell_tx_data["router_address"],
                    2 ** 256 - 1,  # Unlimited approval
                    self.web3,
                    self.fernet
                )
                
                # Wait for approval to be mined
                logger.info(f"Waiting for approval transaction to be mined: {approve_tx}")
                self.web3.eth.wait_for_transaction_receipt(approve_tx)
            
            # Send sell transaction
            sell_tx_hash = self.wallet_manager.send_transaction(
                sell_tx_data["transaction"],
                self.web3,
                self.fernet
            )
            
            logger.info(f"Sell transaction sent: {sell_tx_hash}")
            
            # Wait for transaction to be mined
            sell_receipt = self.web3.eth.wait_for_transaction_receipt(sell_tx_hash)
            
            if sell_receipt["status"] != 1:
                return {
                    "success": False,
                    "message": f"Sell transaction failed: {sell_tx_hash}",
                    "stage": "sell_execution",
                    "buy_tx": buy_tx_hash,
                    "sell_tx": sell_tx_hash
                }
            
            # Get base token balance after arbitrage
            base_balance_after = self.dex_connector.get_token_balance(
                self.base_token_address,
                self.wallet_manager.address
            )
            
            # Calculate actual profit
            token_info = self.dex_connector.get_token_info(self.token_address)
            base_token_info = self.dex_connector.get_token_info(self.base_token_address)
            
            # Calculate gas costs
            buy_gas_used = buy_receipt["gasUsed"]
            sell_gas_used = sell_receipt["gasUsed"]
            
            if "effectiveGasPrice" in buy_receipt:
                buy_gas_price = buy_receipt["effectiveGasPrice"]
                sell_gas_price = sell_receipt["effectiveGasPrice"]
            else:
                buy_gas_price = self.web3.eth.get_transaction(buy_tx_hash)["gasPrice"]
                sell_gas_price = self.web3.eth.get_transaction(sell_tx_hash)["gasPrice"]
            
            buy_gas_cost_wei = buy_gas_used * buy_gas_price
            sell_gas_cost_wei = sell_gas_used * sell_gas_price
            total_gas_cost_wei = buy_gas_cost_wei + sell_gas_cost_wei
            
            # Convert to base token units
            if self.base_token_address == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
                # If base token is native token, gas is already in that unit
                total_gas_cost_base = self.web3.from_wei(total_gas_cost_wei, 'ether')
            else:
                # If base token is not native token, need to convert gas cost
                # This is an approximation
                # TODO: Implement a more accurate conversion
                eth_price = 1  # Replace with actual ETH price
                base_token_price = 1  # Replace with actual base token price
                total_gas_cost_base = (self.web3.from_wei(total_gas_cost_wei, 'ether') * eth_price) / base_token_price
            
            # Calculate actual profit
            initial_amount = opportunity["amount_in"]
            final_amount = base_balance_after["balance"]
            
            profit_amount = final_amount - initial_amount
            profit_pct = (profit_amount / initial_amount) * 100
            
            net_profit = profit_amount - total_gas_cost_base
            net_profit_pct = (net_profit / initial_amount) * 100
            
            end_time = int(time.time())
            execution_time = end_time - start_time
            
            return {
                "success": True,
                "message": f"Arbitrage executed successfully with {net_profit_pct:.2f}% net profit",
                "source_dex": self.source_dex_id,
                "target_dex": self.target_dex_id,
                "token_address": self.token_address,
                "base_token_address": self.base_token_address,
                "initial_amount": initial_amount,
                "final_amount": final_amount,
                "profit_amount": profit_amount,
                "profit_pct": profit_pct,
                "tokens_received": token_balance["balance"],
                "buy_tx": buy_tx_hash,
                "sell_tx": sell_tx_hash,
                "buy_gas_used": buy_gas_used,
                "sell_gas_used": sell_gas_used,
                "total_gas_used": buy_gas_used + sell_gas_used,
                "gas_cost": total_gas_cost_base,
                "net_profit": net_profit,
                "net_profit_pct": net_profit_pct,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Error executing arbitrage: {e}")
            return {
                "success": False,
                "message": f"Error executing arbitrage: {str(e)}",
                "stage": "execution_error"
            }
    
    def _estimate_gas_cost(self) -> Dict[str, Any]:
        """Estimate gas cost for a full arbitrage operation

        Returns:
            Dictionary with gas cost estimates
        """
        try:
            # Estimate gas for buy transaction
            buy_gas_limit = 250000  # Conservative estimate
            
            # Estimate gas for sell transaction
            sell_gas_limit = 250000  # Conservative estimate
            
            # Get gas price
            if hasattr(self.web3.eth, 'max_priority_fee'):
                # EIP-1559
                base_fee = self.web3.eth.get_block('latest')['baseFeePerGas']
                priority_fee = self.web3.eth.max_priority_fee
                gas_price = base_fee + priority_fee
            else:
                # Legacy
                gas_price = self.web3.eth.gas_price
            
            # Calculate total gas cost in native token (ETH, BNB, etc.)
            total_gas_limit = buy_gas_limit + sell_gas_limit
            total_gas_cost_wei = gas_price * total_gas_limit
            total_gas_cost_eth = self.web3.from_wei(total_gas_cost_wei, 'ether')
            
            # If base token is native token, we're done
            if self.base_token_address == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
                total_gas_cost_base = total_gas_cost_eth
            else:
                # If base token is not native token, need to convert gas cost
                # This is an approximation
                # TODO: Implement a more accurate conversion
                eth_price = 1  # Replace with actual ETH price
                base_token_price = 1  # Replace with actual base token price
                total_gas_cost_base = (total_gas_cost_eth * eth_price) / base_token_price
            
            return {
                "success": True,
                "gas_price": gas_price,
                "buy_gas_limit": buy_gas_limit,
                "sell_gas_limit": sell_gas_limit,
                "total_gas_limit": total_gas_limit,
                "total_gas_cost_wei": total_gas_cost_wei,
                "total_gas_cost_eth": total_gas_cost_eth,
                "total_gas_cost_base": total_gas_cost_base
            }
            
        except Exception as e:
            logger.error(f"Error estimating gas cost: {e}")
            return {
                "success": False,
                "error": str(e)
            }

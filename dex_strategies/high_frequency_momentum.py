"""
High-Frequency Momentum Strategy
===============================

A high-risk strategy that attempts to capture rapid price movements in volatile tokens.
This strategy scans multiple tokens for sudden momentum and enters positions with 
tight stop-losses and take-profits.

WARNING: This is an extremely high-risk strategy that can result in significant losses.
Use with extreme caution and only with capital you can afford to lose entirely.
"""

import time
import logging
from typing import Dict, List, Any, Optional
import threading
import math
from web3 import Web3

from dex_strategies.base_strategy import BaseStrategy

logger = logging.getLogger("HFMomentumStrategy")

class HighFrequencyMomentumStrategy(BaseStrategy):
    """
    High-Frequency Momentum Strategy for attempting to capture rapid price movements.
    
    This strategy:
    1. Monitors multiple tokens simultaneously
    2. Looks for sudden price increases with high volume
    3. Enters positions quickly with tight stop-losses
    4. Exits positions with predefined take-profits or stop-losses
    5. Uses a portion of capital for each trade to spread risk
    """
    
    def __init__(self, strategy_id: str, web3: Web3, chain_id: int, **kwargs):
        super().__init__(strategy_id, web3, chain_id, **kwargs)
        
        # Strategy parameters
        self.scan_interval = kwargs.get("scan_interval", 5)  # seconds between scans
        self.momentum_threshold = kwargs.get("momentum_threshold", 3.0)  # % price change to trigger entry
        self.volume_threshold = kwargs.get("volume_threshold", 2.0)  # min volume multiplier vs average
        self.max_slippage = kwargs.get("max_slippage", 3.0)  # maximum allowed slippage %
        self.position_size = kwargs.get("position_size", 0.1)  # % of total capital per trade
        self.max_positions = kwargs.get("max_positions", 3)  # maximum concurrent positions
        self.take_profit = kwargs.get("take_profit", 10.0)  # % profit to take
        self.stop_loss = kwargs.get("stop_loss", 5.0)  # % loss to stop
        self.max_hold_time = kwargs.get("max_hold_time", 600)  # max seconds to hold (10 min)
        self.gas_boost = kwargs.get("gas_boost", 1.5)  # gas price multiplier for fast execution
        
        # Target tokens to scan (if empty, will use provided token list)
        self.target_tokens = kwargs.get("target_tokens", [])
        
        # State variables
        self.is_running = False
        self.active_positions = {}
        self.token_data = {}
        self.stop_event = threading.Event()
        self.scanner_thread = None
        self.trader_thread = None
        
        # Trading history
        self.trade_history = []
        
        logger.info(f"Initialized High-Frequency Momentum Strategy with ID: {strategy_id}")
    
    def start(self) -> Dict[str, Any]:
        """Start the HF Momentum strategy"""
        if self.is_running:
            return {"success": False, "message": "Strategy already running"}
        
        try:
            # Initialize token data
            if not self.target_tokens and self.token_address:
                self.target_tokens = [self.token_address]
                
            if not self.target_tokens:
                return {"success": False, "message": "No target tokens specified"}
            
            # Initialize token data structure
            for token in self.target_tokens:
                self.token_data[token] = {
                    "price_history": [],
                    "volume_history": [],
                    "last_update": 0,
                    "momentum_score": 0,
                    "volume_score": 0
                }
            
            # Start the scanner thread
            self.stop_event.clear()
            self.scanner_thread = threading.Thread(target=self._scanner_loop)
            self.scanner_thread.daemon = True
            self.scanner_thread.start()
            
            # Start the trader thread
            self.trader_thread = threading.Thread(target=self._trader_loop)
            self.trader_thread.daemon = True
            self.trader_thread.start()
            
            self.is_running = True
            logger.info(f"HF Momentum Strategy {self.strategy_id} started")
            
            return {
                "success": True,
                "message": f"HF Momentum Strategy started with {len(self.target_tokens)} tokens",
                "target_tokens": self.target_tokens
            }
            
        except Exception as e:
            logger.error(f"Error starting HF Momentum Strategy: {str(e)}")
            return {"success": False, "message": f"Error starting strategy: {str(e)}"}
    
    def stop(self, force_sell: bool = False) -> Dict[str, Any]:
        """Stop the HF Momentum strategy"""
        if not self.is_running:
            return {"success": False, "message": "Strategy not running"}
        
        try:
            # Signal threads to stop
            self.stop_event.set()
            
            # Wait for threads to finish
            if self.scanner_thread:
                self.scanner_thread.join(timeout=10)
            if self.trader_thread:
                self.trader_thread.join(timeout=10)
            
            # Force sell if requested
            if force_sell and self.active_positions:
                logger.info(f"Force selling {len(self.active_positions)} positions")
                for token, position in list(self.active_positions.items()):
                    self._exit_position(token, "force_sell")
            
            self.is_running = False
            logger.info(f"HF Momentum Strategy {self.strategy_id} stopped")
            
            # Calculate performance
            total_trades = len(self.trade_history)
            profitable_trades = sum(1 for trade in self.trade_history if trade.get("profit_pct", 0) > 0)
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            
            total_profit_pct = sum(trade.get("profit_pct", 0) for trade in self.trade_history)
            avg_profit_pct = total_profit_pct / total_trades if total_trades > 0 else 0
            
            return {
                "success": True,
                "message": "Strategy stopped successfully",
                "performance": {
                    "total_trades": total_trades,
                    "profitable_trades": profitable_trades,
                    "win_rate": win_rate,
                    "total_profit_pct": total_profit_pct,
                    "avg_profit_pct": avg_profit_pct
                }
            }
            
        except Exception as e:
            logger.error(f"Error stopping HF Momentum Strategy: {str(e)}")
            return {"success": False, "message": f"Error stopping strategy: {str(e)}"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the strategy"""
        return {
            "id": self.strategy_id,
            "type": "high_frequency_momentum",
            "is_running": self.is_running,
            "token_address": self.token_address,
            "base_token_address": self.base_token_address,
            "chain_id": self.chain_id,
            "dex_id": self.dex_id,
            "target_tokens": self.target_tokens,
            "active_positions": len(self.active_positions),
            "positions": self.active_positions,
            "trade_history": self.trade_history[-10:],  # Last 10 trades
            "parameters": {
                "scan_interval": self.scan_interval,
                "momentum_threshold": self.momentum_threshold,
                "volume_threshold": self.volume_threshold,
                "take_profit": self.take_profit,
                "stop_loss": self.stop_loss,
                "position_size": self.position_size,
                "max_positions": self.max_positions
            }
        }
    
    def _scanner_loop(self):
        """Main scanner loop that monitors tokens for momentum signals"""
        logger.info(f"Scanner thread started for strategy {self.strategy_id}")
        
        while not self.stop_event.is_set():
            try:
                for token in self.target_tokens:
                    if self.stop_event.is_set():
                        break
                    
                    # Skip tokens that are already in active positions
                    if token in self.active_positions:
                        continue
                    
                    # Get current price and volume data
                    price_data = self._get_token_price_data(token)
                    
                    if price_data.get("success", False):
                        self._update_token_data(token, price_data)
                        
                        # Check for momentum signal
                        signal = self._check_momentum_signal(token)
                        
                        if signal:
                            logger.info(f"Momentum signal detected for {token}")
                            
                            # Check if we can open new position
                            if len(self.active_positions) < self.max_positions:
                                # Queue this token for entry
                                self._enter_position(token)
                    
                # Sleep for scan interval
                time.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"Error in scanner loop: {str(e)}")
                time.sleep(self.scan_interval)
    
    def _trader_loop(self):
        """Main trader loop that manages active positions"""
        logger.info(f"Trader thread started for strategy {self.strategy_id}")
        
        while not self.stop_event.is_set():
            try:
                # Check all active positions
                for token, position in list(self.active_positions.items()):
                    if self.stop_event.is_set():
                        break
                    
                    # Skip if position was just entered
                    if time.time() - position.get("entry_time", 0) < 10:
                        continue
                    
                    # Get current price
                    price_data = self._get_token_price_data(token)
                    
                    if price_data.get("success", False):
                        current_price = price_data.get("price", 0)
                        entry_price = position.get("entry_price", 0)
                        
                        if entry_price > 0 and current_price > 0:
                            # Calculate profit/loss
                            profit_pct = ((current_price / entry_price) - 1) * 100
                            
                            # Update position data
                            self.active_positions[token]["current_price"] = current_price
                            self.active_positions[token]["profit_pct"] = profit_pct
                            self.active_positions[token]["hold_time"] = time.time() - position.get("entry_time", 0)
                            
                            # Check for exit conditions
                            if profit_pct >= self.take_profit:
                                self._exit_position(token, "take_profit")
                            elif profit_pct <= -self.stop_loss:
                                self._exit_position(token, "stop_loss")
                            elif time.time() - position.get("entry_time", 0) >= self.max_hold_time:
                                self._exit_position(token, "max_hold_time")
                
                # Sleep for a short time
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in trader loop: {str(e)}")
                time.sleep(2)
    
    def _get_token_price_data(self, token_address: str) -> Dict[str, Any]:
        """Get price and volume data for a token"""
        try:
            # Use DEX connector to get price data
            price_response = self.dex_connector.get_price_impact(
                self.dex_id,
                self.base_token_address,
                token_address,
                10**16  # 0.01 of base token for price check
            )
            
            if "error" in price_response:
                return {"success": False, "error": price_response["error"]}
            
            # Get basic token info
            token_info = self.dex_connector.get_token_info(token_address)
            
            # Calculate price and estimate volume from liquidity depth
            price = price_response["amount_in_decimal"] / price_response["amount_out_decimal"] if price_response["amount_out_decimal"] > 0 else 0
            
            # Try to estimate volume from price impact
            volume_estimate = price_response.get("reserves_base_token", 0) / 100  # Rough estimate
            
            return {
                "success": True,
                "token_address": token_address,
                "token_symbol": token_info.get("symbol", "UNKNOWN"),
                "price": price,
                "timestamp": int(time.time()),
                "volume_estimate": volume_estimate
            }
            
        except Exception as e:
            logger.error(f"Error getting price data for {token_address}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _update_token_data(self, token_address: str, price_data: Dict[str, Any]):
        """Update token data with new price information"""
        if token_address not in self.token_data:
            self.token_data[token_address] = {
                "price_history": [],
                "volume_history": [],
                "last_update": 0,
                "momentum_score": 0,
                "volume_score": 0
            }
        
        token_data = self.token_data[token_address]
        current_time = int(time.time())
        
        # Only update if sufficient time has passed
        if current_time - token_data["last_update"] >= self.scan_interval:
            # Add new price and volume data
            token_data["price_history"].append({
                "price": price_data.get("price", 0),
                "timestamp": current_time
            })
            
            token_data["volume_history"].append({
                "volume": price_data.get("volume_estimate", 0),
                "timestamp": current_time
            })
            
            # Keep only last 60 data points (5 minutes with 5-second intervals)
            if len(token_data["price_history"]) > 60:
                token_data["price_history"] = token_data["price_history"][-60:]
            if len(token_data["volume_history"]) > 60:
                token_data["volume_history"] = token_data["volume_history"][-60:]
            
            # Update last update time
            token_data["last_update"] = current_time
            
            # Calculate momentum and volume scores
            self._calculate_token_scores(token_address)
    
    def _calculate_token_scores(self, token_address: str):
        """Calculate momentum and volume scores for a token"""
        token_data = self.token_data[token_address]
        prices = token_data["price_history"]
        volumes = token_data["volume_history"]
        
        # Need at least a few data points
        if len(prices) < 6:
            return
        
        # Calculate short-term price change (30 seconds)
        short_term_prices = prices[-6:]
        if short_term_prices[0]["price"] > 0:
            short_term_change = ((short_term_prices[-1]["price"] / short_term_prices[0]["price"]) - 1) * 100
        else:
            short_term_change = 0
        
        # Calculate medium-term price change (1 minute)
        medium_term_prices = prices[-12:] if len(prices) >= 12 else prices
        if medium_term_prices[0]["price"] > 0:
            medium_term_change = ((medium_term_prices[-1]["price"] / medium_term_prices[0]["price"]) - 1) * 100
        else:
            medium_term_change = 0
        
        # Calculate momentum score
        # Higher weight to short-term change for fast response
        momentum_score = (short_term_change * 0.7) + (medium_term_change * 0.3)
        
        # Calculate volume score
        recent_volumes = [v["volume"] for v in volumes[-6:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
        
        # Compare recent volume to average
        if avg_volume > 0:
            volume_ratio = recent_volumes[-1] / avg_volume
        else:
            volume_ratio = 1.0
        
        # Volume score ranges from 0 to 5
        volume_score = min(5, volume_ratio)
        
        # Update scores
        token_data["momentum_score"] = momentum_score
        token_data["volume_score"] = volume_score
    
    def _check_momentum_signal(self, token_address: str) -> bool:
        """Check if a token has a momentum signal"""
        token_data = self.token_data[token_address]
        
        # Need minimum data points
        if len(token_data["price_history"]) < 6:
            return False
        
        # Get scores
        momentum_score = token_data["momentum_score"]
        volume_score = token_data["volume_score"]
        
        # Signal conditions:
        # 1. Momentum exceeds threshold
        # 2. Volume is above threshold
        # 3. Price is increasing (positive momentum)
        
        if (momentum_score >= self.momentum_threshold and 
            volume_score >= self.volume_threshold and 
            momentum_score > 0):
            return True
        
        return False
    
    def _enter_position(self, token_address: str):
        """Enter a new position for a token"""
        try:
            logger.info(f"Entering position for {token_address}")
            
            # Calculate position size based on available capital
            wallet_balance = self._get_wallet_balance()
            
            # Use percentage of available capital
            position_amount = wallet_balance * self.position_size
            
            if position_amount <= 0:
                logger.error(f"Insufficient balance to enter position")
                return False
            
            # Prepare buy transaction with boosted gas
            if self.gas_boost > 1.0:
                chain_id = self.chain_id
                web3 = self.web3
                
                if chain_id == 1:  # Ethereum
                    # Get EIP-1559 gas info
                    gas_info = web3.eth.fee_history(1, 'latest', [50])
                    base_fee = gas_info['baseFeePerGas'][0]
                    priority_fee = gas_info.get('reward', [[0]])[0][0]
                    
                    max_fee = int(base_fee + priority_fee * self.gas_boost)
                    max_priority_fee = int(priority_fee * self.gas_boost)
                    
                    gas_price = {
                        "maxFeePerGas": max_fee,
                        "maxPriorityFeePerGas": max_priority_fee
                    }
                else:
                    # Legacy gas price
                    gas_price = int(web3.eth.gas_price * self.gas_boost)
            else:
                gas_price = "auto"
            
            # Convert amount to wei
            base_token_info = self.dex_connector.get_token_info(self.base_token_address)
            position_amount_wei = int(position_amount * (10 ** base_token_info["decimals"]))
            
            # Execute buy with higher slippage for fast execution
            buy_result = self._execute_swap(
                "buy",
                token_address,
                position_amount_wei,
                self.max_slippage,
                gas_price
            )
            
            if buy_result.get("success", False):
                # Get entry price
                price_data = self._get_token_price_data(token_address)
                entry_price = price_data.get("price", 0) if price_data.get("success", False) else 0
                
                # Record position
                self.active_positions[token_address] = {
                    "entry_time": time.time(),
                    "entry_price": entry_price,
                    "current_price": entry_price,
                    "amount": buy_result.get("amount_purchased", 0),
                    "amount_wei": buy_result.get("amount_purchased_wei", 0),
                    "cost": position_amount,
                    "cost_wei": position_amount_wei,
                    "profit_pct": 0,
                    "hold_time": 0,
                    "transaction_hash": buy_result.get("transaction_hash", "")
                }
                
                logger.info(f"Entered position for {token_address} at price {entry_price}")
                return True
            else:
                logger.error(f"Failed to enter position: {buy_result.get('error', 'Unknown error')}")
                return False
            
        except Exception as e:
            logger.error(f"Error entering position: {str(e)}")
            return False
    
    def _exit_position(self, token_address: str, reason: str):
        """Exit an existing position"""
        try:
            if token_address not in self.active_positions:
                return False
            
            position = self.active_positions[token_address]
            logger.info(f"Exiting position for {token_address} due to {reason}")
            
            # Execute sell with higher slippage for fast execution
            sell_result = self._execute_swap(
                "sell",
                token_address,
                position.get("amount_wei", 0),
                self.max_slippage,
                "auto",  # Use auto gas price for selling
                sell_all=True
            )
            
            if sell_result.get("success", False):
                # Calculate profit/loss
                entry_price = position.get("entry_price", 0)
                exit_price = sell_result.get("price", position.get("current_price", 0))
                
                if entry_price > 0 and exit_price > 0:
                    profit_pct = ((exit_price / entry_price) - 1) * 100
                else:
                    profit_pct = 0
                
                # Record trade in history
                trade_record = {
                    "token_address": token_address,
                    "entry_time": position.get("entry_time", 0),
                    "exit_time": time.time(),
                    "hold_time": time.time() - position.get("entry_time", 0),
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "profit_pct": profit_pct,
                    "cost": position.get("cost", 0),
                    "revenue": sell_result.get("amount_received", 0),
                    "exit_reason": reason
                }
                
                self.trade_history.append(trade_record)
                
                # Remove from active positions
                del self.active_positions[token_address]
                
                logger.info(f"Exited position for {token_address} with {profit_pct:.2f}% profit")
                return True
            else:
                logger.error(f"Failed to exit position: {sell_result.get('error', 'Unknown error')}")
                return False
            
        except Exception as e:
            logger.error(f"Error exiting position: {str(e)}")
            return False
    
    def _execute_swap(self, action, token_address, amount, slippage, gas_price, sell_all=False):
        """Execute a buy or sell swap"""
        try:
            if action == "buy":
                # Prepare buy transaction
                tx_data = self.dex_connector.prepare_buy_transaction(
                    self.dex_id,
                    token_address,
                    amount,
                    self.wallet.address,
                    slippage,
                    self.base_token_address,
                    gas_price,
                    5  # 5 minutes deadline
                )
                
                if "error" in tx_data:
                    return {"success": False, "error": tx_data.get("error")}
                
                # Check if we need approval for ERC20 tokens
                if self.base_token_address != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
                    # Check if token is approved
                    is_approved = self.wallet.is_token_approved(
                        self.base_token_address,
                        tx_data["router_address"],
                        amount,
                        self.web3
                    )
                    
                    if not is_approved:
                        # Approve token
                        logger.info(f"Approving {self.base_token_address} for trading on {self.dex_id}")
                        approve_tx = self.wallet.approve_token(
                            self.base_token_address,
                            tx_data["router_address"],
                            2 ** 256 - 1,  # Unlimited approval
                            self.web3,
                            self.encryption
                        )
                        
                        # Wait for approval to be mined
                        logger.info(f"Waiting for approval transaction to be mined: {approve_tx}")
                        self.web3.eth.wait_for_transaction_receipt(approve_tx)
                
                # Send buy transaction
                tx_hash = self.wallet.send_transaction(
                    tx_data["transaction"],
                    self.web3,
                    self.encryption
                )
                
                logger.info(f"Buy transaction sent: {tx_hash}")
                
                # Wait for transaction to be mined
                receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt["status"] == 1:
                    # Get token balance after purchase
                    token_balance = self.dex_connector.get_token_balance(
                        token_address,
                        self.wallet.address
                    )
                    
                    return {
                        "success": True,
                        "transaction_hash": tx_hash,
                        "block_number": receipt["blockNumber"],
                        "gas_used": receipt["gasUsed"],
                        "token_purchased": token_balance["token"]["symbol"],
                        "amount_purchased": token_balance["balance"],
                        "amount_purchased_wei": token_balance["balance_wei"],
                        "message": f"Successfully purchased {token_balance['balance_formatted']}"
                    }
                else:
                    return {
                        "success": False,
                        "transaction_hash": tx_hash,
                        "error": "Transaction failed on-chain"
                    }
                
            elif action == "sell":
                # For selling, need to handle percent or amount
                if sell_all:
                    # Get token balance
                    token_balance = self.dex_connector.get_token_balance(
                        token_address,
                        self.wallet.address
                    )
                    
                    amount = token_balance["balance_wei"]
                    
                # Prepare sell transaction
                tx_data = self.dex_connector.prepare_sell_transaction(
                    self.dex_id,
                    token_address,
                    amount,
                    self.wallet.address,
                    slippage,
                    self.base_token_address,
                    gas_price,
                    5  # 5 minutes deadline
                )
                
                if "error" in tx_data:
                    return {"success": False, "error": tx_data.get("error")}
                
                # Check if token is approved for router
                is_approved = self.wallet.is_token_approved(
                    token_address,
                    tx_data["router_address"],
                    amount,
                    self.web3
                )
                
                if not is_approved:
                    # Approve token
                    logger.info(f"Approving {token_address} for trading on {self.dex_id}")
                    approve_tx = self.wallet.approve_token(
                        token_address,
                        tx_data["router_address"],
                        2 ** 256 - 1,  # Unlimited approval
                        self.web3,
                        self.encryption
                    )
                    
                    # Wait for approval to be mined
                    logger.info(f"Waiting for approval transaction to be mined: {approve_tx}")
                    self.web3.eth.wait_for_transaction_receipt(approve_tx)
                
                # Send sell transaction
                tx_hash = self.wallet.send_transaction(
                    tx_data["transaction"],
                    self.web3,
                    self.encryption
                )
                
                logger.info(f"Sell transaction sent: {tx_hash}")
                
                # Wait for transaction to be mined
                receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt["status"] == 1:
                    # Get base token information
                    base_token_info = self.dex_connector.get_token_info(self.base_token_address)
                    
                    # Calculate approximately how much base token was received
                    amount_received = tx_data["estimation"]["amount_out_units"]
                    
                    return {
                        "success": True,
                        "transaction_hash": tx_hash,
                        "block_number": receipt["blockNumber"],
                        "gas_used": receipt["gasUsed"],
                        "amount_received": amount_received,
                        "amount_received_wei": tx_data["estimation"]["amount_out"],
                        "message": f"Successfully sold for approximately {amount_received} {base_token_info['symbol']}"
                    }
                else:
                    return {
                        "success": False,
                        "transaction_hash": tx_hash,
                        "error": "Transaction failed on-chain"
                    }
            
        except Exception as e:
            logger.error(f"Error executing swap: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_wallet_balance(self) -> float:
        """Get wallet balance of base token"""
        try:
            if self.base_token_address == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
                # Native token balance
                balance_wei = self.web3.eth.get_balance(self.wallet.address)
                decimals = 18
            else:
                # ERC20 token balance
                token_info = self.dex_connector.get_token_info(self.base_token_address)
                balance = self.dex_connector.get_token_balance(
                    self.base_token_address,
                    self.wallet.address
                )
                balance_wei = int(balance["balance_wei"])
                decimals = token_info["decimals"]
            
            # Convert to decimal
            balance = balance_wei / (10 ** decimals)
            
            # Reserve some for gas
            if self.base_token_address == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
                # Reserve 0.01 ETH for gas if using native token
                balance = max(0, balance - 0.01)
            
            return balance
            
        except Exception as e:
            logger.error(f"Error getting wallet balance: {str(e)}")
            return 0.0

import json
from web3 import Web3
from eth_account import Account

# Uniswap V2 Router ABI (truncated for swapExactETHForTokens)
UNISWAP_V2_ROUTER_ABI = [
    {
        "name": "swapExactETHForTokens",
        "type": "function",
        "inputs": [
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "outputs": [
            {"name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "payable"
    }
]


def buy_token(
    web3: Web3,
    router_address: str,
    private_key: str,
    token_in: str,
    token_out: str,
    amount_in_wei: int,
    amount_out_min_wei: int,
    to_address: str,
    deadline: int
) -> str:
    """
    Executes a Uniswap V2 buy (swapExactETHForTokens) transaction.
    Args:
        web3: Web3 instance
        router_address: Uniswap V2 router contract address
        private_key: Buyer's private key
        token_in: Address of input token (usually WETH)
        token_out: Address of output token
        amount_in_wei: Amount of ETH to swap (in wei)
        amount_out_min_wei: Minimum amount of tokens to receive (in wei)
        to_address: Recipient address
        deadline: Unix timestamp after which the tx will revert
    Returns:
        Transaction hash
    """
    acct = Account.from_key(private_key)
    router = web3.eth.contract(address=router_address, abi=UNISWAP_V2_ROUTER_ABI)
    path = [web3.to_checksum_address(token_in), web3.to_checksum_address(token_out)]
    txn = router.functions.swapExactETHForTokens(
        amount_out_min_wei,
        path,
        to_address,
        deadline
    ).build_transaction({
        'from': acct.address,
        'value': amount_in_wei,
        'gas': 300000,
        'gasPrice': web3.eth.gas_price,
        'nonce': web3.eth.get_transaction_count(acct.address)
    })
    signed = web3.eth.account.sign_transaction(txn, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    return web3.to_hex(tx_hash)

# Example usage (for reference only, not executed on import)
if __name__ == "__main__":
    # Setup Web3
    w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_INFURA_KEY"))
    router = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  # Uniswap V2 router
    priv_key = "YOUR_PRIVATE_KEY"
    weth = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    token = "0x..."  # Token to buy
    amount_in = w3.to_wei(0.01, 'ether')
    amount_out_min = 0  # Set appropriately
    to = "0x..."  # Your address
    deadline = int(time.time()) + 60 * 10
    tx = buy_token(w3, router, priv_key, weth, token, amount_in, amount_out_min, to, deadline)
    print(f"Tx sent: {tx}")

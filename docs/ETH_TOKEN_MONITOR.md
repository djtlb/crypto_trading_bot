# ETH Token Monitor

This module provides real-time monitoring of new ETH-based tokens on decentralized exchanges and identifies arbitrage opportunities.

## Features

- **Real-time monitoring** of new token pairs with WETH or USDT
- **Filtering** of token pairs based on base and quote tokens
- **Arbitrage detection** between different DEXes
- **GPU-accelerated analysis** for token price data
- **WebSocket integration** with Moralis for live blockchain events

## Usage

### Starting the ETH Token Monitor

Run the provided example script to start monitoring for new ETH-based tokens:

```bash
python examples/eth_token_monitor.py
```

### Programmatic Usage

```python
from utils.gpu_acceleration import GPUAccelerator

# Initialize the GPU accelerator
gpu_accel = GPUAccelerator()

# Start monitoring for new ETH-based tokens
def token_callback(token_data):
    print(f"New token detected: {token_data.get('baseToken', {}).get('symbol')}")
    
# Start monitoring with a minimum liquidity threshold
ws = gpu_accel.monitor_eth_based_tokens(
    callback=token_callback,
    min_liquidity_usd=10000  # $10k minimum liquidity
)

# Find arbitrage opportunities for a specific token
# (filtering for WETH or USDT pairs is automatic)
token_address = "0x0000000000000000000000000000000000000000"  # Replace with actual token address
opportunities = gpu_accel.find_arbitrage_opportunities(
    token_address=token_address,
    chain_id="ethereum",
    min_price_diff_percent=1.0  # 1% minimum price difference
)
```

## API Endpoints

This module integrates with the following DexScreener API endpoints:

- Token profiles: `https://api.dexscreener.com/token-profiles/latest/v1`
- Token boosts: `https://api.dexscreener.com/token-boosts/latest/v1`
- Token boosts top: `https://api.dexscreener.com/token-boosts/top/v1`
- Orders: `https://api.dexscreener.com/orders/v1`
- DEX pairs: `https://api.dexscreener.com/latest/dex/pairs`
- DEX search: `https://api.dexscreener.com/latest/dex/search`
- Token pairs: `https://api.dexscreener.com/token-pairs/v1`
- Tokens: `https://api.dexscreener.com/tokens/v1`

## Moralis WebSocket Integration

The module connects to Moralis WebSocket at:
```
wss://ws.moralis.io/mainnet?apiKey=your_api_key
```

This connection provides real-time updates on new token pair creations.

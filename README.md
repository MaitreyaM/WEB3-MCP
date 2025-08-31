# Web3 MCP Server

A Model Context Protocol (MCP) server for Ethereum blockchain operations, deployed on Smithery.ai using Streamable HTTP transport.

## Features

- **Wallet Management**: Check wallet balances and send ETH transactions
- **Token Operations**: Get ERC-20 token balances and prices
- **DeFi Integration**: Wrap ETH to WETH and swap tokens on Uniswap V3
- **Smart Contract Interaction**: Generic contract function calls
- **Price Feeds**: Real-time ETH/USD price from Chainlink (soon)
- **Multi-Network Support**: Sepolia testnet and Ethereum mainnet

## Available Tools

### 1. `get_wallet_balance`
Get the native ETH balance of any wallet address.

### 2. `get_token_price`
Get real-time ETH/USD price from Chainlink price feeds.

### 3. `send_eth`
Send ETH from the agent wallet to any address.

### 4. `interact_with_contract`
Call any function on any smart contract (read or write).

### 5. `get_erc20_balance`
Check ERC-20 token balances for any wallet.

### 6. `wrap_eth`
Convert native ETH to WETH (Wrapped ETH).

### 7. `swap_tokens_for_tokens`
Swap tokens on Uniswap V3 with automatic approval.

## Deployment on Smithery.ai

This server is configured for deployment on Smithery.ai using Streamable HTTP transport.

### Required Configuration

The server requires the following environment variables:

- `WEB3_PROVIDER_URL`: Your Ethereum RPC endpoint (e.g., Infura, Alchemy)
- `AGENT_PRIVATE_KEY`: Private key for the agent wallet (without 0x prefix)


### Network-Specific Addresses

#### Sepolia Testnet (Default)
- WETH Contract: `0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14`
- Uniswap Router: `0x3bFA4769FB09eefC5a399D6D47036A5d3fA67B54`
- ETH/USD Price Feed: `0x694AA1769357215DE4FAC081bf1f309aDC325306`

#### Ethereum Mainnet
- WETH Contract: `0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2`
- Uniswap Router: `0xE592427A0AEce92De3Edee1F18E0157C05861564`
- ETH/USD Price Feed: `0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419`

### Port Configuration

The server runs on port 3000 and is configured for container deployment.

## Local Development

### Prerequisites

1. Python 3.10+
2. Ethereum RPC endpoint (Infura, Alchemy, or local node)
3. Private key for testing wallet

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export WEB3_PROVIDER_URL="https://sepolia.infura.io/v3/YOUR_PROJECT_ID"
   export AGENT_PRIVATE_KEY="your_private_key_without_0x"
   export NETWORK="sepolia"  # or "mainnet"
   ```

3. **Run the server:**
   ```bash
   python server.py
   ```

### Environment Variables

Create a `.env` file in the project root:

```env
WEB3_PROVIDER_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID
AGENT_PRIVATE_KEY=your_private_key_without_0x
NETWORK=sepolia
```

## Docker Deployment

### Build Image

```bash
docker build -t web3-mcp-server .
```

### Run Container

```bash
docker run -p 3000:3000 \
  -e WEB3_PROVIDER_URL="https://sepolia.infura.io/v3/YOUR_PROJECT_ID" \
  -e AGENT_PRIVATE_KEY="your_private_key_without_0x" \
  -e NETWORK="sepolia" \
  web3-mcp-server
```

## Security Considerations


- Use environment variables for all sensitive data
- Consider using a dedicated wallet for the MCP server
- Regularly rotate private keys
- Monitor wallet balances and transactions
- Use testnet for development and testing

## Error Handling

The server includes comprehensive error handling:

- Connection validation to Web3 providers
- Transaction timeout handling (5 minutes default)
- Input validation for addresses and amounts
- Graceful error responses with detailed messages
- Logging for debugging and monitoring

## Network Support

- **Sepolia Testnet**: Recommended for development and testing
- **Ethereum Mainnet**: Production use (use with caution)

## Dependencies

- `fastmcp`: MCP server framework
- `web3`: Ethereum blockchain interaction
- `python-dotenv`: Environment variable management
- `requests`: HTTP request handling

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check your RPC endpoint URL and network connectivity
2. **Insufficient Balance**: Ensure the agent wallet has enough ETH for gas fees
3. **Transaction Failed**: Check gas prices and network congestion
4. **Invalid Address**: Ensure addresses are valid Ethereum addresses

### Debug Mode

Enable debug logging by setting the log level in the code:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Support

For deployment issues on Smithery.ai, refer to their documentation and support channels.

For blockchain-related issues, check:
- Your RPC provider's status page
- Network gas prices and congestion
- Contract addresses and ABIs



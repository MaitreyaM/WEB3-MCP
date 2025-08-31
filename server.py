from mcp.server.fastmcp import FastMCP
import os
from web3 import Web3
import json
import logging
from functools import wraps
from typing import Optional
import time
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "web3_server",
    host="localhost",
    port=3000,
    stateless_http=True,
)

# Environment variables with validation
REQUIRED_ENV_VARS = ["WEB3_PROVIDER_URL", "AGENT_PRIVATE_KEY"]
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise ValueError(f"Required environment variable {var} is not set")

WEB3_PROVIDER_URL = os.getenv("WEB3_PROVIDER_URL")
AGENT_PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")

# Network-specific configurations
NETWORK_CONFIG = {
    "sepolia": {
        "WETH_CONTRACT_ADDRESS": "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
        "UNISWAP_ROUTER_ADDRESS": "0x3bFA4769FB09eefC5a399D6D47036A5d3fA67B54",
        "CHAINLINK_ETH_USD_PRICE_FEED_ADDRESS": "0x694AA1769357215DE4FAC081bf1f309aDC325306",
    },
    "mainnet": {
        "WETH_CONTRACT_ADDRESS": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "UNISWAP_ROUTER_ADDRESS": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "CHAINLINK_ETH_USD_PRICE_FEED_ADDRESS": "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",
    }
}

# Get network from env or default to sepolia
NETWORK = os.getenv("NETWORK", "sepolia").lower()
if NETWORK not in NETWORK_CONFIG:
    raise ValueError(f"Unsupported network: {NETWORK}")

config = NETWORK_CONFIG[NETWORK]
WETH_CONTRACT_ADDRESS = config["WETH_CONTRACT_ADDRESS"]
UNISWAP_ROUTER_ADDRESS = config["UNISWAP_ROUTER_ADDRESS"]
CHAINLINK_ETH_USD_PRICE_FEED_ADDRESS = config["CHAINLINK_ETH_USD_PRICE_FEED_ADDRESS"]

# ABIs remain the same
CHAINLINK_PRICE_FEED_ABI = """
[
  {
    "inputs": [],
    "name": "latestRoundData",
    "outputs": [
      { "internalType": "uint80", "name": "roundId", "type": "uint80" },
      { "internalType": "int256", "name": "answer", "type": "int256" },
      { "internalType": "uint256", "name": "startedAt", "type": "uint256" },
      { "internalType": "uint256", "name": "updatedAt", "type": "uint256" },
      { "internalType": "uint80", "name": "answeredInRound", "type": "uint80" }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "decimals",
    "outputs": [{ "internalType": "uint8", "name": "", "type": "uint8" }],
    "stateMutability": "view",
    "type": "function"
  }
]
"""

ERC20_STANDARD_ABI = """
[
  {"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
  {"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
  {"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}
]
"""

WETH_ABI = """
[
  {"constant":false,"inputs":[],"name":"deposit","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},
  {"constant":true,"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}
]
"""

UNISWAP_ABI = """
[{"inputs":[{"components":[{"type":"address","name":"tokenIn"},{"type":"address","name":"tokenOut"},{"type":"uint24","name":"fee"},{"type":"address","name":"recipient"},{"type":"uint256","name":"amountIn"},{"type":"uint256","name":"amountOutMinimum"},{"type":"uint160","name":"sqrtPriceLimitX96"}],"type":"tuple","name":"params"}],"name":"exactInputSingle","outputs":[{"type":"uint256","name":"amountOut"}],"stateMutability":"payable","type":"function"}]
"""

# Global variables
w3: Optional[Web3] = None
agent_account = None

def error_handler(func):
    """Decorator for consistent error handling and logging."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {type(e).__name__} - {e}")
            return f"Error in {func.__name__}: {type(e).__name__} - {e}"
    return wrapper

def _initialize_web3():
    """Initializes Web3 instance and account with connection validation."""
    global w3, agent_account
    if w3 is None:
        try:
            w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))
            
            # Validate connection
            if not w3.is_connected():
                raise ConnectionError("Failed to connect to Web3 provider")
            
            # Validate network
            chain_id = w3.eth.chain_id
            logger.info(f"Connected to network with chain ID: {chain_id}")
            
            agent_account = w3.eth.account.from_key(AGENT_PRIVATE_KEY)
            logger.info(f"Agent address: {agent_account.address}")
            
        except Exception as e:
            logger.error(f"Web3 initialization failed: {e}")
            raise

def _wait_for_transaction_with_timeout(tx_hash, timeout=300):
    """Wait for transaction with timeout and better error handling."""
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        if receipt.status == 0:
            raise Exception(f"Transaction {w3.to_hex(tx_hash)} failed")
        return receipt
    except Exception as e:
        logger.error(f"Transaction {w3.to_hex(tx_hash)} failed or timed out: {e}")
        raise

@mcp.tool('get_wallet_balance')
@error_handler
def get_wallet_balance(address: str) -> str:
    """Gets the native token balance of a given wallet address."""
    _initialize_web3()
    
    if not w3.is_address(address):
        return f"Error: Invalid address format: {address}"
    
    balance_wei = w3.eth.get_balance(address)
    balance_eth = w3.from_wei(balance_wei, 'ether')
    return f"The balance of address {address} is {balance_eth} ETH."

@mcp.tool('get_token_price')
@error_handler
def get_token_price(token_pair: str) -> str:
    """Gets the latest price of a token pair from Chainlink Price Feed."""
    _initialize_web3()
    
    if token_pair.upper() != "ETH/USD":
        return "Error: This tool currently only supports the 'ETH/USD' token pair."

    price_feed_contract = w3.eth.contract(
        address=CHAINLINK_ETH_USD_PRICE_FEED_ADDRESS,
        abi=json.loads(CHAINLINK_PRICE_FEED_ABI)
    )
    
    latest_data = price_feed_contract.functions.latestRoundData().call()
    price_raw = latest_data[1]
    updated_at = latest_data[3]
    
    # Check if price is stale (older than 1 hour)
    if time.time() - updated_at > 3600:
        logger.warning("Price feed data may be stale")
    
    price_decimals = price_feed_contract.functions.decimals().call()
    price = price_raw / (10 ** price_decimals)
    
    return f"The latest price for {token_pair} is ${price:.2f}"

@mcp.tool('send_eth')
@error_handler
def send_eth(to_address: str, amount_eth: float) -> str:
    """Creates, signs, and sends a transaction to transfer ETH."""
    _initialize_web3()
    
    if not w3.is_address(to_address):
        return f"Error: Invalid recipient address: {to_address}"
    
    if amount_eth <= 0:
        return "Error: Amount must be greater than 0"
    
    # Check balance
    balance = w3.eth.get_balance(agent_account.address)
    amount_wei = w3.to_wei(amount_eth, 'ether')
    
    if balance < amount_wei:
        return f"Error: Insufficient balance. Available: {w3.from_wei(balance, 'ether')} ETH"
    
    nonce = w3.eth.get_transaction_count(agent_account.address)
    gas_price = w3.eth.gas_price
    
    tx = {
        'from': agent_account.address,
        'to': to_address,
        'value': amount_wei,
        'gas': 21000,
        'gasPrice': gas_price,
        'nonce': nonce,
    }

    signed_tx = w3.eth.account.sign_transaction(tx, AGENT_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    logger.info(f"Transaction sent: {w3.to_hex(tx_hash)}")
    return f"Transaction sent successfully. Hash: {w3.to_hex(tx_hash)}"

@mcp.tool('interact_with_contract')
@error_handler
def interact_with_contract(
    contract_address: str,
    abi: str,
    function_name: str,
    function_args: list,
    is_write_transaction: bool = False
) -> str:
    """Interacts with a smart contract by calling one of its functions."""
    _initialize_web3()

    if not w3.is_address(contract_address):
        return f"Error: Invalid contract address: {contract_address}"
    
    try:
        abi_json = json.loads(abi)
    except json.JSONDecodeError:
        return "Error: Invalid ABI JSON format"

    contract = w3.eth.contract(address=contract_address, abi=abi_json)
    
    if not hasattr(contract.functions, function_name):
        return f"Error: Function '{function_name}' not found in contract ABI"

    func_to_call = getattr(contract.functions, function_name)
    prepared_func = func_to_call(*function_args)

    if is_write_transaction:
        nonce = w3.eth.get_transaction_count(agent_account.address)
        tx = prepared_func.build_transaction({
            'from': agent_account.address,
            'nonce': nonce,
            'gasPrice': w3.eth.gas_price
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=AGENT_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info(f"Write transaction sent: {w3.to_hex(tx_hash)}")
        return f"Write transaction sent. Hash: {w3.to_hex(tx_hash)}"
    else:
        result = prepared_func.call()
        return json.dumps(result, default=str)

@mcp.tool('get_erc20_balance')
@error_handler
def get_erc20_balance(token_address: str, wallet_address: str) -> str:
    """Gets the balance of a specific ERC-20 token for a given wallet."""
    _initialize_web3()
    
    if not w3.is_address(token_address) or not w3.is_address(wallet_address):
        return "Error: Invalid address format"
    
    chk_token_address = Web3.to_checksum_address(token_address)
    chk_wallet_address = Web3.to_checksum_address(wallet_address)
    
    token_contract = w3.eth.contract(address=chk_token_address, abi=json.loads(ERC20_STANDARD_ABI))
    
    decimals = token_contract.functions.decimals().call()
    raw_balance = token_contract.functions.balanceOf(chk_wallet_address).call()
    
    balance = raw_balance / (10 ** decimals)
    return str(balance)

@mcp.tool('wrap_eth')
@error_handler
def wrap_eth(amount_eth: float) -> str:
    """Converts native ETH into WETH by depositing into the WETH contract."""
    _initialize_web3()
    
    if amount_eth <= 0:
        return "Error: Amount must be greater than 0"
    
    weth_contract = w3.eth.contract(address=WETH_CONTRACT_ADDRESS, abi=json.loads(WETH_ABI))
    
    tx = weth_contract.functions.deposit().build_transaction({
        'from': agent_account.address,
        'value': w3.to_wei(amount_eth, 'ether'),
        'nonce': w3.eth.get_transaction_count(agent_account.address),
        'gasPrice': w3.eth.gas_price
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=AGENT_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    logger.info(f"Wrap transaction sent: {w3.to_hex(tx_hash)}")
    _wait_for_transaction_with_timeout(tx_hash)
    
    return f"ETH wrapping successful. Hash: {w3.to_hex(tx_hash)}"

@mcp.tool('swap_tokens_for_tokens')
@error_handler
def swap_tokens_for_tokens(token_in_address: str, token_out_address: str, amount_in: float, fee: int = 3000) -> str:
    """Swaps tokens on Uniswap V3 with proper validation and confirmation."""
    _initialize_web3()
    
    if amount_in <= 0:
        return "Error: Amount must be greater than 0"
    
    if not w3.is_address(token_in_address) or not w3.is_address(token_out_address):
        return "Error: Invalid token address format"
    
    chk_token_in = Web3.to_checksum_address(token_in_address)
    chk_token_out = Web3.to_checksum_address(token_out_address)
    chk_router_address = Web3.to_checksum_address(UNISWAP_ROUTER_ADDRESS)
    
    token_in_contract = w3.eth.contract(address=chk_token_in, abi=json.loads(ERC20_STANDARD_ABI))
    decimals = token_in_contract.functions.decimals().call()
    amount_in_wei = int(amount_in * (10**decimals))

    # Check token balance
    balance = token_in_contract.functions.balanceOf(agent_account.address).call()
    if balance < amount_in_wei:
        return f"Error: Insufficient token balance. Available: {balance / (10**decimals)}"

    current_nonce = w3.eth.get_transaction_count(agent_account.address)

    # Step 1: Approve
    approve_tx = token_in_contract.functions.approve(chk_router_address, amount_in_wei).build_transaction({
        'from': agent_account.address, 
        'nonce': current_nonce,
        'gasPrice': w3.eth.gas_price
    })
    
    signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, private_key=AGENT_PRIVATE_KEY)
    approve_tx_hash = w3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
    
    logger.info(f"Approval transaction sent: {w3.to_hex(approve_tx_hash)}")
    _wait_for_transaction_with_timeout(approve_tx_hash)

    # Step 2: Swap
    uniswap_router = w3.eth.contract(address=chk_router_address, abi=json.loads(UNISWAP_ABI))
    swap_params = (chk_token_in, chk_token_out, fee, agent_account.address, amount_in_wei, 0, 0)
    
    swap_tx = uniswap_router.functions.exactInputSingle(swap_params).build_transaction({
        'from': agent_account.address, 
        'nonce': current_nonce + 1,
        'gasPrice': w3.eth.gas_price
    })
    
    signed_swap_tx = w3.eth.account.sign_transaction(swap_tx, private_key=AGENT_PRIVATE_KEY)
    swap_tx_hash = w3.eth.send_raw_transaction(signed_swap_tx.raw_transaction)

    logger.info(f"Swap transaction sent: {w3.to_hex(swap_tx_hash)}")
    _wait_for_transaction_with_timeout(swap_tx_hash)
    
    return f"Swap successful. Hash: {w3.to_hex(swap_tx_hash)}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
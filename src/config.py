import os

# Proof-of-Work difficulty (number of leading zeros required)
# Set lower for development/testing; higher = slower mining = more secure
DIFFICULTY = int(os.getenv("BC_DIFFICULTY", 3))

# Reward given to the miner who successfully mines a block
MINING_REWARD = float(os.getenv("BC_REWARD", 10.0))

# Sentinel sender address for coinbase/reward transactions
MINER_ADDRESS = "NETWORK"

# Default host for Flask nodes
DEFAULT_HOST = "0.0.0.0"

# Default port (can be overridden via --port flag)
DEFAULT_PORT = int(os.getenv("BC_PORT", 5000))

# Optional persistence (disabled by default for predictable test/demo behavior)
PERSIST_BLOCKCHAIN = os.getenv("BC_PERSIST", "0") == "1"
BLOCKCHAIN_DATA_DIR = os.getenv("BC_DATA_DIR", ".data")
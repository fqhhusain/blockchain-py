#!/usr/bin/env bash
# demo.sh - Human-friendly end-to-end demo flow for the blockchain API.
#
# Default behavior assumes nodes are already running.
# You can enable auto-start with AUTO_START_NODES=1.
#
# Examples:
#   bash demo.sh
#   RECEIVER=Bob AMOUNT=7.5 MINER_ADDRESS=Alice bash demo.sh
#   AUTO_START_NODES=1 WAIT_AFTER_START=4 bash demo.sh

set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage:
  bash demo.sh

Config via environment variables:
  NODE1              Default: http://localhost:5000
  NODE2              Default: http://localhost:5001
  NODE3              Default: http://localhost:5002
  RECEIVER           Default: Bob
  AMOUNT             Default: 5.0
  MINER_ADDRESS      Default: DemoMiner
  AUTO_START_NODES   Default: 0 (set 1 to run run_nodes.sh automatically)
  WAIT_AFTER_START   Default: 3 (seconds)
EOF
  exit 0
fi

NODE1="${NODE1:-http://localhost:5000}"
NODE2="${NODE2:-http://localhost:5001}"
NODE3="${NODE3:-http://localhost:5002}"
RECEIVER="${RECEIVER:-Bob}"
AMOUNT="${AMOUNT:-5.0}"
MINER_ADDRESS="${MINER_ADDRESS:-DemoMiner}"
AUTO_START_NODES="${AUTO_START_NODES:-0}"
WAIT_AFTER_START="${WAIT_AFTER_START:-3}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_NODES_SH="$ROOT_DIR/run_nodes.sh"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

require_cmd curl
require_cmd python

NODES_PID=""
cleanup() {
  if [[ -n "$NODES_PID" ]]; then
    echo ""
    echo "Stopping background nodes started by demo.sh ..."
    kill "$NODES_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if [[ "$AUTO_START_NODES" == "1" ]]; then
  if [[ ! -x "$RUN_NODES_SH" && ! -f "$RUN_NODES_SH" ]]; then
    echo "Cannot find run_nodes.sh at: $RUN_NODES_SH"
    exit 1
  fi

  echo "Starting 3 nodes in background ..."
  bash "$RUN_NODES_SH" >/tmp/blockchain-demo-nodes.log 2>&1 &
  NODES_PID=$!
  sleep "$WAIT_AFTER_START"
fi

health_check() {
  local url="$1"
  if ! curl -fsS "$url/chain" >/dev/null; then
    echo "Node is not reachable: $url"
    echo "Tip: run 'bash run_nodes.sh' or set AUTO_START_NODES=1"
    exit 1
  fi
}

echo "Checking node availability ..."
health_check "$NODE1"
health_check "$NODE2"
health_check "$NODE3"

echo ""
echo "=== DEMO PARAMETERS ==="
echo "NODE1=$NODE1"
echo "NODE2=$NODE2"
echo "NODE3=$NODE3"
echo "RECEIVER=$RECEIVER"
echo "AMOUNT=$AMOUNT"
echo "MINER_ADDRESS=$MINER_ADDRESS"

echo ""
echo "1) Generate wallet on NODE1"
WALLET_JSON="$(curl -fsS "$NODE1/wallet/new")"

echo "2) Build signed transaction payload"
export WALLET_JSON RECEIVER AMOUNT
TX_JSON="$(python - <<'PY'
import binascii
import json
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

wallet = json.loads(os.environ["WALLET_JSON"])
receiver = os.environ["RECEIVER"]
amount = float(os.environ["AMOUNT"])

payload = {
    "sender": wallet["address"],
    "receiver": receiver,
    "amount": amount,
}

private_key = serialization.load_pem_private_key(
    wallet["private_key"].encode("utf-8"),
    password=None,
    backend=default_backend(),
)
message = json.dumps(payload, sort_keys=True).encode("utf-8")
signature = binascii.hexlify(
    private_key.sign(message, ec.ECDSA(hashes.SHA256()))
).decode("utf-8")

payload["signature"] = signature
payload["public_key"] = wallet["public_key"]

print(json.dumps(payload))
PY
)"

echo "3) Submit signed transaction to NODE1"
TX_RESP="$(curl -fsS -X POST "$NODE1/transactions/new" -H "Content-Type: application/json" -d "$TX_JSON")"
printf '%s\n' "$TX_RESP"

echo ""
echo "4) Mine block on NODE1"
MINE_RESP="$(curl -fsS -X POST "$NODE1/mine" -H "Content-Type: application/json" -d "{\"miner_address\":\"$MINER_ADDRESS\"}")"
printf '%s\n' "$MINE_RESP"

echo ""
echo "5) Resolve consensus on NODE2 and NODE3"
RESOLVE2="$(curl -fsS "$NODE2/nodes/resolve")"
RESOLVE3="$(curl -fsS "$NODE3/nodes/resolve")"

echo "NODE2 resolve:"
printf '%s\n' "$RESOLVE2"
echo "NODE3 resolve:"
printf '%s\n' "$RESOLVE3"

echo ""
echo "6) Final summary"
export NODE1 NODE2 NODE3 MINER_ADDRESS RECEIVER
python - <<'PY'
import json
import os
import urllib.request

node1 = os.environ["NODE1"]
node2 = os.environ["NODE2"]
node3 = os.environ["NODE3"]
miner = os.environ["MINER_ADDRESS"]
receiver = os.environ["RECEIVER"]

def get_json(url: str):
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))

c1 = get_json(f"{node1}/chain")
c2 = get_json(f"{node2}/chain")
c3 = get_json(f"{node3}/chain")
bm = get_json(f"{node1}/balance/{miner}")
br = get_json(f"{node1}/balance/{receiver}")

print("Chain lengths:")
print(f"  node1={c1['length']} node2={c2['length']} node3={c3['length']}")
print("Balances on NODE1:")
print(f"  {miner}={bm['balance']}")
print(f"  {receiver}={br['balance']}")
PY

echo ""
echo "Demo completed successfully."

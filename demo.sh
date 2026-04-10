#!/usr/bin/env bash
# demo.sh - Structured end-to-end demo flow for the blockchain API.

set -Eeuo pipefail

# -----------------------------
# Config (env-overridable)
# -----------------------------
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
NODES_LOG="${TMPDIR:-/tmp}/blockchain-demo-nodes.log"

NODES_PID=""

usage() {
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
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

cleanup() {
  if [[ -n "${NODES_PID:-}" ]]; then
    echo ""
    echo "Stopping background nodes started by demo.sh ..."
    kill "$NODES_PID" 2>/dev/null || true
  fi
}

post_json() {
  local url="$1"
  local body="$2"
  curl -fsS -X POST "$url" -H "Content-Type: application/json" -d "$body"
}

health_check_one() {
  local url="$1"
  if ! curl -fsS "$url/chain" >/dev/null; then
    die "Node is not reachable: $url (Tip: run bash run_nodes.sh or set AUTO_START_NODES=1)"
  fi
}

check_all_nodes() {
  echo "Checking node availability ..."
  health_check_one "$NODE1"
  health_check_one "$NODE2"
  health_check_one "$NODE3"
}

start_nodes_if_needed() {
  if [[ "$AUTO_START_NODES" != "1" ]]; then
    return
  fi

  [[ -f "$RUN_NODES_SH" ]] || die "Cannot find run_nodes.sh at: $RUN_NODES_SH"

  echo "Starting 3 nodes in background ..."
  bash "$RUN_NODES_SH" >"$NODES_LOG" 2>&1 &
  NODES_PID=$!
  sleep "$WAIT_AFTER_START"
}

print_params() {
  echo ""
  echo "=== DEMO PARAMETERS ==="
  echo "NODE1=$NODE1"
  echo "NODE2=$NODE2"
  echo "NODE3=$NODE3"
  echo "RECEIVER=$RECEIVER"
  echo "AMOUNT=$AMOUNT"
  echo "MINER_ADDRESS=$MINER_ADDRESS"
}

build_signed_tx_json() {
  local wallet_json="$1"

  WALLET_JSON="$wallet_json" RECEIVER="$RECEIVER" AMOUNT="$AMOUNT" python - <<'PY'
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
}

show_final_summary() {
  NODE1="$NODE1" NODE2="$NODE2" NODE3="$NODE3" MINER_ADDRESS="$MINER_ADDRESS" RECEIVER="$RECEIVER" python - <<'PY'
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
}

main() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
  fi

  require_cmd curl
  require_cmd python
  trap cleanup EXIT INT TERM

  start_nodes_if_needed
  check_all_nodes
  print_params

  echo ""
  echo "1) Generate wallet on NODE1"
  local wallet_json
  wallet_json="$(curl -fsS "$NODE1/wallet/new")"

  echo "2) Build signed transaction payload"
  local tx_json
  tx_json="$(build_signed_tx_json "$wallet_json")"

  echo "3) Submit signed transaction to NODE1"
  local tx_resp
  tx_resp="$(post_json "$NODE1/transactions/new" "$tx_json")"
  printf '%s\n' "$tx_resp"

  echo ""
  echo "4) Mine block on NODE1"
  local mine_resp
  mine_resp="$(post_json "$NODE1/mine" "{\"miner_address\":\"$MINER_ADDRESS\"}")"
  printf '%s\n' "$mine_resp"

  echo ""
  echo "5) Resolve consensus on NODE2 and NODE3"
  local resolve2 resolve3
  resolve2="$(curl -fsS "$NODE2/nodes/resolve")"
  resolve3="$(curl -fsS "$NODE3/nodes/resolve")"

  echo "NODE2 resolve:"
  printf '%s\n' "$resolve2"
  echo "NODE3 resolve:"
  printf '%s\n' "$resolve3"

  echo ""
  echo "6) Final summary"
  show_final_summary

  echo ""
  echo "Demo completed successfully."
}

main "$@"
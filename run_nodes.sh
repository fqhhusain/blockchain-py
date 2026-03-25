#!/usr/bin/env bash
# run_nodes.sh — Start 3 independent blockchain nodes
# Usage: bash run_nodes.sh
# Each node runs on a separate port: 5000, 5001, 5002
# Press Ctrl+C to stop all nodes.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/src"

# Trap Ctrl+C to kill all background processes cleanly
cleanup() {
  echo ""
  echo "🛑 Stopping all nodes..."
  kill "$PID1" "$PID2" "$PID3" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

echo "=========================================="
echo "  🔗 Blockchain — 3-Node Local Network"
echo "=========================================="
echo ""
echo "  Node 1 → http://localhost:5000"
echo "  Node 2 → http://localhost:5001"
echo "  Node 3 → http://localhost:5002"
echo ""
echo "  Press Ctrl+C to stop all nodes."
echo "=========================================="
echo ""

cd "$SRC"

# Start Node 1 (port 5000)
BC_PORT=5000 python app.py --port 5000 &
PID1=$!
echo "✅ Node 1 started (PID $PID1)"

sleep 1

# Start Node 2 (port 5001)
BC_PORT=5001 python app.py --port 5001 &
PID2=$!
echo "✅ Node 2 started (PID $PID2)"

sleep 1

# Start Node 3 (port 5002)
BC_PORT=5002 python app.py --port 5002 &
PID3=$!
echo "✅ Node 3 started (PID $PID3)"

echo ""
echo "All nodes running. Registering peers..."
sleep 2

# Register peers on each node (full mesh)
curl -s -X POST http://localhost:5000/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["localhost:5001", "localhost:5002"]}' > /dev/null && \
  echo "✅ Node 1 peers registered"

curl -s -X POST http://localhost:5001/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["localhost:5000", "localhost:5002"]}' > /dev/null && \
  echo "✅ Node 2 peers registered"

curl -s -X POST http://localhost:5002/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["localhost:5000", "localhost:5001"]}' > /dev/null && \
  echo "✅ Node 3 peers registered"

echo ""
echo "🌐 Network ready! Open Postman and import src/postman_collection.json"
echo ""

# Wait for any background job to exit
wait
#!/bin/bash

ORDER_CONTAINERS=("order_service_1" "order_service_2" "order_service_3")
COMPOSE_PREFIX="spring25-lab3-spring25-lab3-shireenmeher"
NUM_ITERATIONS=4
FRONTEND_URL="http://frontend_service:8000"
ORDER_IDS_LOG="logs/placed_orders.log"
PORTS=(6001 6002 6003)

echo "[START SIMULATION TEST] Starting crash simulation test..."
echo "[BACKGROUND_PROCESS] Launching client in background..."
python3 client.py crash_failure 1 0.5 & 
CLIENT_PID=$!

sleep 5

# Step 1: Force a crash on the known leader (order_service_3)
LEADER_NAME="order_service_3"
LEADER_FULL_NAME="${COMPOSE_PREFIX}-${LEADER_NAME}-1"
echo ""
echo "------------------------------------------"
echo "[LEADER CRASH] [$(date)] Implemenmting leader crash: $LEADER_FULL_NAME"
echo "------------------------------------------"
docker stop "$LEADER_FULL_NAME"
sleep 3
docker start "$LEADER_FULL_NAME"
sleep 5

# Step 2: Randomly crash other replicas
for i in $(seq 1 $NUM_ITERATIONS); do
  echo ""
  echo "🔁 [$(date)] Iteration $i: Simulating random crash..."

  RANDOM_INDEX=$(( RANDOM % 3 ))
  CONTAINER_NAME="${ORDER_CONTAINERS[$RANDOM_INDEX]}"
  FULL_NAME="${COMPOSE_PREFIX}-${CONTAINER_NAME}-1"
  echo "------------------------------------------"
  echo "[STOP][$(date)] Stopping $FULL_NAME..."
  echo "------------------------------------------"
  docker stop "$FULL_NAME"
  

  sleep 3

  echo "------------------------------------------"
  echo "[[START] $(date)] Restarting $FULL_NAME..."
  echo "------------------------------------------"
  docker start "$FULL_NAME"

  sleep 4
done

# Step 3: Wait for client to finish
wait $CLIENT_PID

echo ""
echo "--------------------------------------------------------------------"
echo "Crash simulation complete."
echo "--------------------------------------------------------------------"

# Step 4: Check consistency of placed orders across replicas
echo ""
echo "------------------------------------------"
echo "Starting consistency check..."
echo "------------------------------------------"

if [ ! -f "$ORDER_IDS_LOG" ]; then
  echo "Order log file not found: $ORDER_IDS_LOG"
  exit 1
fi

while IFS= read -r order_id; do
  echo ""
  echo "------------------------------------------"
  echo " Checking order: $order_id"
  echo "------------------------------------------"

  reference=""
  consistent=true

  for i in "${!ORDER_CONTAINERS[@]}"; do
    replica="${ORDER_CONTAINERS[$i]}"
    port="${PORTS[$i]}"
    url="http://${replica}:${port}/orders/${order_id}"

    response=$(curl -s "$url" | jq -S .data)

    echo "$replica response: $response"

    if [ -z "$reference" ]; then
      reference="$response"
    elif [ "$response" != "$reference" ]; then
      consistent=false
    fi
  done

  if $consistent; then
    echo "------------------------------------------"
    echo "Order $order_id is consistent across replicas"
    echo "------------------------------------------"
  else
    echo "------------------------------------------"
    echo "Order $order_id is INCONSISTENT across replicas"
    echo "------------------------------------------"
  fi
done < "$ORDER_IDS_LOG"

echo ""
echo "------------------------------------------"
echo "Consistency check complete."
echo "------------------------------------------"

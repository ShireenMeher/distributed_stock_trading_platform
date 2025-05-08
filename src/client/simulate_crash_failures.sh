# #!/bin/bash

# ORDER_CONTAINERS=("order_service_1" "order_service_2" "order_service_3")
# COMPOSE_PREFIX="spring25-lab3-spring25-lab3-shireenmeher"  # Adjust if your prefix differs
# NUM_ITERATIONS=5
# FRONTEND_URL="http://frontend_service:8000"

# # Step 1: Run client in background
# echo "🚀 Starting client in background..."
# python3 client.py cached 1 0.5 &  # or any mode you want to test
# CLIENT_PID=$!

# sleep 5  # give client a head start

# # Step 2: Randomly stop and restart replicas
# for i in $(seq 1 $NUM_ITERATIONS); do
#   echo ""
#   echo "🔁 Iteration $i: Simulating crash..."

#   # Pick a random order service
#   RANDOM_INDEX=$(( RANDOM % 3 ))
#   CONTAINER_NAME="${ORDER_CONTAINERS[$RANDOM_INDEX]}"
#   FULL_NAME="${COMPOSE_PREFIX}-${CONTAINER_NAME}-1"

#   echo "🛑 Stopping $FULL_NAME..."
#   docker stop "$FULL_NAME"

#   sleep 3

#   echo "♻️ Restarting $FULL_NAME..."
#   docker start "$FULL_NAME"

#   sleep 4
# done

# # Step 3: Wait for client to finish
# wait $CLIENT_PID

# echo "✅ Crash simulation complete."
# 2
#!/bin/bash

FRONTEND_URL="http://frontend_service:8000"
FOLLOWER_URL="http://order_service_2:6002"

echo " [STOP] Stopping order_service_2..."
docker stop spring25-lab3-spring25-lab3-shireenmeher-order_service_2-1
sleep 2

echo "📦 Sending trade request {"name": "MenhirCo", "type": "sell", "quantity": 5} ..."
response=$(curl -s -X POST "$FRONTEND_URL/orders" \
  -H "Content-Type: application/json" \
  -d '{"name": "MenhirCo", "type": "sell", "quantity": 5}')

echo "[RESPONSE] Raw Response: $response"

# Extract the transaction ID (adjust this path as needed based on actual JSON)
txn_id=$(echo "$response" | jq -r '.data.transaction_number')

echo "[TRANSACTION_ID] Trade submitted with txn_id=$txn_id"

echo "[RESTART] Restarting order_service_2..."
docker start spring25-lab3-spring25-lab3-shireenmeher-order_service_2-1
sleep 5

echo "[VALIDATION] Verifying sync on follower..."
verify_response=$(curl -s -w "%{http_code}" -o temp_response.json "$FOLLOWER_URL/orders/$txn_id")

echo "-----------------"
echo "$verify_response"
echo "-----------------"

if [ "$verify_response" = "200" ]; then
  echo "[SYNC_SUCCESS!!!] Follower recovered and synced transaction $txn_id"
  cat temp_response.json
else
  echo "[SYNC_FAILURE] Follower did not sync transaction. HTTP $verify_response"
fi

rm -f temp_response.json

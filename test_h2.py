#!/usr/bin/env python3
"""
Script: Verify H2
Purpose: Taking the Ferrari for a spin on the Autobahn.
"""
import sys
import os

# 1. Hook up the framework
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

from core.requester import Requester
from core.logger import logger
from core.config import config

# 2. Force the Engine to verify SSL (Real sites require valid SSL for H2)
# We override the lab setting temporarily
config.VERIFY_SSL = True 
config.FORCE_HTTP2 = True      # <--- ADD THIS! FORCE THE SWITCH! 🟢

def test_connection():
    logger.info("🏎️  Warming up the HTTP/2 Engine...")
    
    # Initialize the Sanchez Requester
    req = Requester()

    # Target: Google (They invented HTTP/2 basically, so they definitely support it)
    target = "https://0a0400040404510d805ff85a00e400a8.web-security-academy.net"
    
    logger.info(f"🎯 Target locked: {target}")
    
    # Fire the shot
    # We expect the Requester to see "https" and "FORCE_HTTP2" logic (or auto-negotiate)
    # Note: To guarantee H2, you can also set config.FORCE_HTTP2 = True locally
    
    res = req.get(target)

    if res:
        # Check specific protocol version on the response object
        # httpx response has .http_version
        # requests response does NOT have .http_version (usually)
        
        try:
            # If it's HTTPX (H2)
            version = res.http_version
            logger.info(f"✅ Protocol Used: {version}")
            
            if version == "HTTP/2":
                logger.success("🔥 TEST PASSED: WE ARE RUNNING ON HTTP/2!")
            else:
                logger.warning("⚠️  Connected, but using HTTP/1.1 (Did you install httpx[http2]?)")
                
        except AttributeError:
            # If it's Requests (H1)
            logger.warning("⚠️  Fallback Active: Response came from 'requests' (HTTP/1.1)")
    else:
        logger.critical("❌ Connection Failed.")

if __name__ == "__main__":
    test_connection()
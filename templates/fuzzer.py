#!/usr/bin/env python3
"""
Module: Fuzzer (The Striker)
Purpose: Active fuzzing for LFI, RCE, etc.
"""
import sys
import os
import urllib.parse
from pathlib import Path

# ———— IMPORT FIX (The Band-Aid) ————
# This allows 'python3 templates/fuzzer.py' to work
sys.path.append(str(Path(__file__).resolve().parent)) 
from base_template import get_base_parser, run_scan

# Link to Core
sys.path.append(str(Path(__file__).resolve().parents[1]))
from core import logger

def check(target_input: str, base_url: str, req, **kwargs) -> str | None:
    """
    The Attack Logic.
    """
    # ———— 1. ENCODING (Crucial!) ————
    # Remember the 400 Bad Request error? We fix it here.
    if "{PAYLOAD}" in base_url:
        encoded_payload = urllib.parse.quote(target_input, safe='')
        url = base_url.replace("{PAYLOAD}", encoded_payload)
    else:
        # Append mode
        url = f"{base_url}{target_input}"

    # ———— 2. FIRE ————
    try:
        # req is the Persistent Engine passed from base_template
        res = req.get(url, allow_redirects=False)
        
        if not res: return None

        # ———— 3. DETECTION ————
        # LFI
        if "root:x:0:0:" in res.text or "[boot loader]" in res.text:
            return f"🔥 LFI FOUND: {url}"
        
        # RCE
        if "uid=" in res.text and "gid=" in res.text:
             return f"🚨 RCE CONFIRMED: {url}"

        # Error Based SQLi (Bonus)
        if "You have an error in your SQL syntax" in res.text:
             return f"💉 SQLi HINT: {url}"

    except Exception:
        pass
    
    return None

def main():
    # We inherit the parser from the Mother Template
    parser = get_base_parser("FUZZER")
    
    # [TACTICAL NOTE]: If you wanted to add specific args just for Fuzzer,
    # you would do: parser.add_argument("--fuzz-mode", ...) here.
    
    args = parser.parse_args()
    
    # Run the match
    run_scan("FUZZER", check, args)

if __name__ == "__main__":
    main()
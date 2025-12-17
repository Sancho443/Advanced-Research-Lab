#!/usr/bin/env python3
"""
Module: Fuzzer (The Striker)
Purpose: Active fuzzing for LFI, RCE, etc.
"""
import sys
import urllib.parse
from pathlib import Path

# ———— ROBUST IMPORT FIX ————
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from templates.base_template import get_base_parser, run_scan
from core import logger

def check(target_input: str, base_url: str, session, **kwargs) -> str | None:
    """
    The Attack Logic.
    """
    # ———— 1. PAYLOAD PLACEMENT ————
    if "{PAYLOAD}" in base_url:
        # Injection Mode (e.g. ?id={PAYLOAD})
        # We generally encode here to be safe, but LFI sometimes hates encoding.
        # Let's trust the wordlist. If user wants encoded, use an encoded wordlist.
        # But to prevent crashing the URL parser, we safely quote specific chars if needed.
        # For now, let's inject RAW to allow power-user payloads like '../../'
        url = base_url.replace("{PAYLOAD}", target_input)
    else:
        # Append Mode (Directory Fuzzing)
        if not base_url.endswith("/"):
            base_url += "/"
        # Strip leading slash from payload to avoid double //
        payload = target_input.lstrip("/")
        url = f"{base_url}{payload}"

    # ———— 2. FIRE ————
    try:
        # session is the Persistent Engine passed from base_template
        res = session.get(url, allow_redirects=False)
        
        if not res: return None

        # ———— 3. DETECTION ————
        
        # LFI (Linux)
        if "root:x:0:0:" in res.text:
             return f"🔥 LFI FOUND (passwd): {url}"
        
        # LFI (Windows)
        if "[boot loader]" in res.text or "win.ini" in res.text:
             return f"🔥 LFI FOUND (win.ini): {url}"
        
        # RCE (Linux)
        if "uid=" in res.text and "gid=" in res.text and "groups=" in res.text:
             return f"🚨 RCE CONFIRMED: {url}"

        # Error Based SQLi (Bonus)
        sql_errors = [
            "You have an error in your SQL syntax",
            "Warning: mysql_",
            "Unclosed quotation mark",
            "ORA-01756" 
        ]
        if any(err in res.text for err in sql_errors):
             return f"💉 SQLi HINT: {url}"

    except Exception:
        pass
    
    return None

def main():
    parser = get_base_parser("FUZZER")
    args = parser.parse_args()
    
    # Validation
    if not args.wordlist:
         logger.critical("❌ Fuzzer requires a payload wordlist (-w)!")
         sys.exit(1)

    run_scan("FUZZER", check, args)

if __name__ == "__main__":
    main()
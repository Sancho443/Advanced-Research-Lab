#!/usr/bin/env python3
"""
Module: [TOOL NAME]
Author: Sanchez (The Architect)
Purpose: [WHAT DOES IT HUNT?]
"""

import argparse
import sys
import os
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colors
init(autoreset=True)

# ———— 1. THE CONNECTION (Crucial) ————
# This tells Python: "Look upstairs for the 'core' folder."
# Without this, 'from core import...' crashes.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# ———— 2. THE IMPORTS (The Squad) ————
# Requester: Handles HTTP, Proxies, User-Agents, Headers automatically.
# engine: Handles Threading and Progress Bars.
# logger: Handles printing to the screen and log file.
# config: Handles global settings (Timeouts, Delays).
# get_banner: The cool ASCII art.
from core import engine, logger, config, get_banner, Requester

# ———— 3. THE BRAIN (The Logic) ————
def check_vulnerability(payload: str, base_url: str) -> str | None:
    """
    The Logic Function.
    INPUT: A single payload string and the target URL.
    OUTPUT: A success string (if vuln found) or None (if safe).
    """
    req = Requester()
    
    # A. Build the Target
    # Decide how to inject the payload (Append? Replace?)
    target = f"{base_url}{payload}" 

    # B. Fire the Shot
    try:
        res = req.get(target) # or req.post(target, data=...)
    except Exception:
        return None # Network error = miss

    if not res:
        return None

    # C. Analyze the Result (The VAR Check)
    # This is where YOU write the specific detection logic.
    if "root:x:0:0" in res.text:  # <--- REPLACE THIS WITH YOUR LOGIC
        return f"{Fore.GREEN}VULN FOUND: {payload}{Style.RESET_ALL}"

    return None

# ———— 4. THE MANAGER (CLI) ————
def get_arg_parser() -> argparse.ArgumentParser:
    desc = get_banner("[TOOL NAME]")
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawTextHelpFormatter)

    # Standard Args
    parser.add_argument("-u", "--url", required=True, help="Target URL")
    parser.add_argument("-w", "--wordlist", required=True, help="Payload Wordlist")
    
    # Standard Tactics (Threads/Delay)
    parser.add_argument("-t", "--threads", type=int, default=10, help="Threads")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay (sec)")
    parser.add_argument("--header", action="append", default=[], help="Custom Headers")

    return parser

# ———— 5. THE KICKOFF ————
def main():
    parser = get_arg_parser()
    args = parser.parse_args()
    print(get_banner("[TOOL NAME]"))

    # A. Configure the Engine
    object.__setattr__(config, "THREADS", args.threads)
    object.__setattr__(config, "DELAY", args.delay)
    
    # B. Configure Headers (Cookie Injection)
    headers = {}
    for h in args.headers:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = v.strip()
    object.__setattr__(config, "CUSTOM_HEADERS", headers)

    # C. Load Ammo
    path = Path(args.wordlist).expanduser().resolve()
    if not path.exists():
        logger.critical(f"Wordlist not found: {path}")
        sys.exit(1)
    payloads = [line.strip() for line in path.read_text().splitlines() if line.strip()]

    # D. Start the Engine
    logger.info(f"Starting Scan on {args.url}...")
    
    hits = engine.run(
        task_function=check_vulnerability, # <--- Pass your function here
        targets=payloads,
        base_url=args.url,
        desc="Scanning..."
    )

    # E. Victory Lap
    if hits:
        print()
        logger.info(f"🔥 FOUND {len(hits)} HITS!")
        for hit in hits:
            print(f"   {hit}")
    else:
        logger.info("✅ Target seems safe.")

if __name__ == "__main__":
    main()
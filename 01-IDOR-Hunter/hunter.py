#!/usr/bin/env python3
# Module: hunter.py
#!/usr/bin/env python3
"""
01-IDOR-Hunter/hunter.py
Author: Sanchez (The Playmaker) + Grok (The Ruthless Coach)
Purpose: Proper IDOR/BOLA hunter with threading, smart diffing, and no amateur mistakes.
"""

import argparse
import sys
import os
import json
from pathlib import Path
from functools import partial
from typing import Optional, List, Dict, Any
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Path hack to find 'core'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core import engine, logger, config, get_banner, Requester


def check_idor(
    payload: str,
    base_url_template: str,
    method: str,
    data_template: Optional[str],
    baseline_response: Optional[str] = None
) -> Optional[str]:
    """
    Smart IDOR check: injects payload, compares response size/content, filters noise.
    """
    req = Requester()

    # 1. Build target URL
    target_url = base_url_template.replace("{PAYLOAD}", payload)

    # 2. Build request data (smart JSON handling if needed)
    target_data = None
    if data_template:
        if "{PAYLOAD}" in data_template:
            try:
                # Proper JSON substitution instead of string replace (Senior Dev Move)
                data_json = json.loads(data_template.replace("{PAYLOAD}", payload))
                target_data = json.dumps(data_json)
            except json.JSONDecodeError:
                # Fallback to string replace if not valid JSON (e.g. form-data)
                target_data = data_template.replace("{PAYLOAD}", payload)
        else:
            target_data = data_template

    try:
        # Note: Requester handles the actual method call dynamically
        response = req.request(method.upper(), target_url, data=target_data)
        if not response:
            return None
    except Exception as e:
        logger.debug(f"Request failed for {payload}: {e}")
        return None

    status = response.status_code
    size = len(response.text)

    # ———— NOISE FILTERS ————
    if status in (400, 404, 405):
        return None  # Expected failures (Invalid ID)

    if status == 401:
        return f"{Fore.RED}{payload} → 401 Unauthorized (Auth Header missing?){Style.RESET_ALL}"

    if status == 403:
        # Sometimes 403 leaks more than 200 — worth flagging if it's uniquely large
        if size > 1000:
            return f"{Fore.YELLOW}{payload} → 403 but juicy ({size}b){Style.RESET_ALL}"
        return None

    # ———— SUCCESS ANALYSIS ————
    if status in (200, 201, 202):
        # Advanced: Compare against baseline to detect "False 200s" (Soft 404s)
        if baseline_response:
            diff = abs(size - len(baseline_response))
            # If size is almost identical to the error page, ignore it
            if diff < 50: 
                return None
            
            return f"{Fore.GREEN}{payload} → {status} | LEAK? Size: {size}b (Diff: {diff}){Style.RESET_ALL}"
        
        # Fallback: Just check size if no baseline
        elif size > 800:  
            return f"{Fore.CYAN}{payload} → {status} | Size: {size}b{Style.RESET_ALL}"

    return None


def establish_baseline(url: str, method: str, data: Optional[str]) -> Optional[str]:
    """Get a baseline response using a known-invalid payload (e.g. 0 or 'nonexistent')"""
    logger.info("📡 Establishing baseline with dummy payload...")
    req = Requester()
    
    # We inject a dummy ID "0" to see what a "Not Found" or "Forbidden" looks like
    test_url = url.replace("{PAYLOAD}", "0")
    test_data = None
    
    if data:
        test_data = data.replace("{PAYLOAD}", "0")

    try:
        resp = req.request(method, test_url, data=test_data)
        if resp:
            logger.info(f"   Baseline established. Status: {resp.status_code}, Size: {len(resp.text)}b")
            return resp.text
    except:
        logger.warning("   Failed to establish baseline. Running blind.")
    return None


def get_arg_parser() -> argparse.ArgumentParser:
    desc = get_banner("IDOR / BOLA Hunter v2")
    #print(f"{Fore.RED}{config.BANNER}{Style.RESET_ALL}")
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawTextHelpFormatter)

    # Target
    g = parser.add_argument_group(f'{Fore.RED}TARGET{Style.RESET_ALL}')
    g.add_argument("-u", "--url", required=True, help="URL with {PAYLOAD} placeholder")
    g.add_argument("-m", "--method", default="GET", help="HTTP method (GET, POST, PUT, DELETE)")
    g.add_argument("-d", "--data", help="JSON/body data with {PAYLOAD}")

    # Payloads (Fixed Logic)
    g = parser.add_argument_group(f'{Fore.YELLOW}PAYLOADS{Style.RESET_ALL}')
    g.add_argument("--start", type=int, help="Start ID (Range Mode)")
    g.add_argument("--end", type=int, help="End ID (Range Mode)")
    g.add_argument("-w", "--wordlist", help="Wordlist file (UUID Mode)")

    # Auth & Tactics
    g = parser.add_argument_group(f'{Fore.GREEN}AUTH & TACTICS{Style.RESET_ALL}')
    g.add_argument("--header", action="append", default=[], help="Headers: Cookie: ..., Authorization: Bearer ...")
    g.add_argument("--delay", type=float, default=0.0, help="Delay between requests")
    g.add_argument("-t", "--threads", type=int, default=15, help="Thread count")

    return parser


def main():
    parser = get_arg_parser()
    args = parser.parse_args()

    print(get_banner("IDOR / BOLA Hunter v2"))

    # ———— VALIDATION (The Referee) ————
    if args.wordlist:
        if args.start is not None or args.end is not None:
            logger.critical("❌ Logic Error: Cannot use --wordlist with --start/--end")
            sys.exit(1)
    else:
        if args.start is None or args.end is None:
            logger.critical("❌ Logic Error: Must provide BOTH --start and --end (or use --wordlist)")
            sys.exit(1)

    # ———— CONFIG OVERRIDES ————
    object.__setattr__(config, "DELAY", args.delay)
    object.__setattr__(config, "THREADS", args.threads)

    # ———— HEADERS & CONTENT-TYPE ————
    headers = {}
    for h in args.headers:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = v.strip()
    
    # Auto-add JSON header if we are sending data but forgot the header
    if args.data and "content-type" not in {k.lower() for k in headers}:
        headers["Content-Type"] = "application/json"
        logger.info("💉 Auto-injecting 'Content-Type: application/json'")
    
    object.__setattr__(config, "CUSTOM_HEADERS", headers)

    # ———— PAYLOAD GENERATION ————
    if args.wordlist:
        path = Path(args.wordlist).expanduser().resolve()
        if not path.exists():
            logger.critical(f"Wordlist not found: {path}")
            sys.exit(1)
        payloads = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    else:
        payloads = [str(i) for i in range(args.start, args.end + 1)]

    logger.info(f"Loaded {len(payloads)} payloads | Threads: {args.threads} | Method: {args.method}")

    # ———— BASELINE ————
    baseline = establish_baseline(args.url, args.method, args.data)

    # ———— TASK WRAPPER ————
    # We wrap the function to pass the static arguments (url, method, data) 
    # while the engine only passes the dynamic argument (payload)
    def task_wrapper(payload: str):
        return check_idor(
            payload=payload,
            base_url_template=args.url,
            method=args.method,
            data_template=args.data,
            baseline_response=baseline
        )
    # Fix logging name so it looks professional
    task_wrapper.__name__ = "check_idor"

    # ———— KICK OFF ————
    hits = engine.run(
        task_function=task_wrapper,
        targets=payloads,
        desc=f"IDOR Hunt"
    )

    if hits:
        print()
        logger.info(f"🎯 IDOR CONFIRMED | {len(hits)} Hits Found")
        for hit in hits[:10]:
            print(f"   {hit}")
    else:
        print()
        logger.warning("🧱 Wall of Steel. No IDORs found.")

if __name__ == "__main__":
    main()
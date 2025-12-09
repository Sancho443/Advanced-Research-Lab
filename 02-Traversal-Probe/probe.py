#!/usr/bin/env python3
"""
02-Traversal-Probe/probe.py
Author: Sanchez (The Architect)
Purpose: Path Traversal Fuzzer with a Help Menu that looks better
"""

import argparse
import sys
import os
from pathlib import Path
from colorama import Fore, Style, init


# Initialize colorama for Windows users (prevents weird symbols)
init(autoreset=True)

# ———— THE NECESSARY CRIME 🕵️‍♂️ ————
# Ensures we can import 'core' and 'modules' from the root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core import engine, logger, config, get_banner
from modules.traversal import check_traversal

def parse_headers(header_string: str) -> dict:
    """Parse multiple 'Key: Value' headers (Copy-Paste from Striker)."""
    if not header_string:
        return {}

    headers = {}
    # Split by newline, semicolon, or comma
    parts = [p.strip() for p in header_string.replace(';', '\n').replace(',', '\n').split('\n') if p.strip()]

    for part in parts:
        if ':' not in part:
            continue
        key, value = part.split(":", 1)
        headers[key.strip()] = value.strip()
        # Log the injection so we know it worked
        logger.info(f"💉 Injected header → {Fore.CYAN}{key.strip()}: {value.strip()[:30]}...{Style.RESET_ALL}")

    return headers 

def load_payloads(filepath: str | Path) -> list[str]:
    """Load and clean payloads from wordlist."""
    path = Path(filepath).expanduser().resolve()
    if not path.is_file():
        logger.critical(f"Wordlist missing: {path}")
        sys.exit(1)

    payloads = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    logger.info(f"Loaded {len(payloads):,} payloads ← {path.name}")
    return payloads

def get_arg_parser() -> argparse.ArgumentParser:
    #take note of this desc,,,causes some weird errors,,,don't know why
    desc = f"""
{Fore.RED}      
   {Style.RESET_ALL}
{Fore.YELLOW}{Style.RESET_ALL}

    """
# 1. The Description (The Drip 💧)
    # Notice we use {{PAYLOAD}} to escape the braces inside the f-string
    # 2. The Examples (The Tactics Board 📋)
    examples = f"""{Fore.CYAN}EXAMPLES:{Style.RESET_ALL}
  {Fore.GREEN}# 1. The Standard Attack{Style.RESET_ALL}
  python3 probe.py -u "http://target.com/load?file={{PAYLOAD}}" -w payloads/basic.txt

  {Fore.GREEN}# 2. The Stealth Run (2s Delay){Style.RESET_ALL}
  python3 probe.py -u "http://target.com/img?id={{PAYLOAD}}" -w payloads/encoded.txt --delay 2.0

  {Fore.GREEN}# 3. The Blitz (50 Threads){Style.RESET_ALL}
  python3 probe.py -u "http://target.com/doc?f={{PAYLOAD}}" -w payloads.txt -t 50
    """

    # 3. The Setup
    parser = argparse.ArgumentParser(
        description=desc,
        epilog=examples,
        formatter_class=argparse.RawTextHelpFormatter
    )

    # 4. Argument Groups
    target_group = parser.add_argument_group(f'{Fore.RED}TARGETING{Style.RESET_ALL}')
    target_group.add_argument("-u", "--url", required=True, 
                        help="Target URL. Use {PAYLOAD} as the injection marker.")
    target_group.add_argument("-w", "--wordlist", required=True, 
                        help="Path to the payload wordlist.")
    # 👇 NEW: Auth Support
    target_group.add_argument("--header", "--headers", dest="headers", action="append", default=[],
                        help="Add header(s). Ex: --header 'Cookie: id=1'")
    

    tactics_group = parser.add_argument_group(f'{Fore.BLUE}TACTICS{Style.RESET_ALL}')
    tactics_group.add_argument("--delay", type=float, 
                        help="Time wasting tactics (seconds between requests).")
    tactics_group.add_argument("-t", "--threads", type=int, default=10,
                        help="Pressing intensity (default: 10).")

    return parser



if __name__ == "__main__":

    print(get_banner("seek and you shall find"))

    args = get_arg_parser().parse_args()

    # ———— TACTICAL OVERRIDES ————
    if args.delay is not None:
        object.__setattr__(config, "DELAY", args.delay)
        logger.info(f"Delay → {args.delay}s (stealth mode engaged)")

    if args.threads:
        object.__setattr__(config, "THREADS", args.threads)
        logger.info(f"Threads → {args.threads} (full send)")
# 👇 NEW: HEADER INJECTION LOGIC
    if args.headers:
        all_headers = {}
        for h in args.headers:
            all_headers.update(parse_headers(h))
        
        # Inject into Global Config
        object.__setattr__(config, "CUSTOM_HEADERS", all_headers)

    logger.info(f"Target locked: {args.url}")

    payloads = load_payloads(args.wordlist)
    if not payloads:
        logger.error("Empty payload list. Can't fight with no ammo.")
        sys.exit(1)

    # ———— KICK OFF ————
    hits = engine.run(
        task_function=check_traversal,
        targets=payloads,
        base_url=args.url,
        desc="Path Traversal"
    )

    # ———— VICTORY CEREMONY ————
    if hits:
        print()
        logger.info(f"TRAVERSAL ACHIEVED | {len(hits)} HITS")
        for i, hit in enumerate(hits[:15], 1):
            logger.info(f"  {i:2d}. {hit}")
        if len(hits) > 15:
            logger.info(f"  ... and {len(hits) - 15} more sleeping in the logs")
        print()
        logger.info("Go collect your flags, king.")
    else:
        logger.warning("Access denied. Defense was too strong.")
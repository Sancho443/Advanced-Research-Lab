#!/usr/bin/env python3
# Module: striker.py
import sys
import os
import argparse
from pathlib import Path
from colorama import Fore, Style # <--- MOVED TO TOP (Global Scope)

# Path Hack
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core import engine, logger, config, get_banner
from modules.ssrf import check_ssrf

def parse_headers(header_string: str) -> dict:
    """Parse multiple 'Key: Value' headers, even from Burp copy-paste."""
    if not header_string:
        return {}

    headers = {}
    # Split by common separators: newline, semicolon, comma (Burp users rejoice)
    parts = [p.strip() for p in header_string.replace(';', '\n').replace(',', '\n').split('\n') if p.strip()]

    for part in parts:
        if ':' not in part:
            logger.warning(f"Skipping invalid header (no ':'): {part}")
            continue
        key, value = part.split(":", 1)
        key = key.strip()
        value = value.strip()
        headers[key] = value
        
        # Now this works because Fore is imported globally
        logger.info(f"Injected header → {Fore.CYAN}{key}: {value[:30]}{'...' if len(value)>30 else ''}{Style.RESET_ALL}")

    return headers

def get_arg_parser():
    # Helper to get the base arguments (threads, delay, etc)
    parser = engine.get_arg_parser(description="Sanchez SSRF Striker - The Cloud Hunter")
    
    parser.add_argument("-u", "--url", required=True, 
                        help="Target URL with {PAYLOAD} marker")
    parser.add_argument("-w", "--wordlist", required=True, 
                        help="Path to payload file")
    
    # 👇 The "Curl Style" header flag
    parser.add_argument("--header", "--headers", dest="headers", action="append", default=[],
                    help="Add header(s). Ex: --header 'Cookie: id=1' --header 'Authorization: Bearer xyz'")
    
    return parser

if __name__ == "__main__":
    print(get_banner("SSRF Striker v1.0"))
    

    parser = get_arg_parser()
    args = parser.parse_args()

    # 1. Inject Headers into the Global Config
    if args.headers:
        all_headers = {}
        for h in args.headers:
            all_headers.update(parse_headers(h))
        
        # Bypass the frozen config using the "God Mode" setattr
        object.__setattr__(config, "CUSTOM_HEADERS", all_headers)

    # 2. Load Payloads
    path = Path(args.wordlist).expanduser().resolve()
    if not path.exists():
        logger.critical(f"Wordlist not found: {path}")
        sys.exit(1)
        
    payloads = [line.strip() for line in path.read_text().splitlines() if line.strip()]

    # 3. Kick Off
    engine.run(
        task_function=check_ssrf,
        targets=payloads,
        base_url=args.url,
        desc="SSRF Striker"
    )
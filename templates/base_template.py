#!/usr/bin/env python3
"""
The Arsenal Base Template — Fixed & Optimized.
"""
import argparse
import sys
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

# Robust Path Fixing (Works even if called from sub-sub-folders)
# Finds the 'core' folder by looking up until it finds it
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import engine, logger, config, get_banner, Requester

def get_base_parser(tool_name: str) -> argparse.ArgumentParser:
    desc = get_banner(tool_name)
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawTextHelpFormatter)

    # TARGET
    g_target = parser.add_argument_group('🎯 Target')
    g_target.add_argument("-u", "--url", required=True, help="Target URL (use {PAYLOAD} marker)")

    # PAYLOADS
    g_payload = parser.add_argument_group('💣 Payloads')
    g_payload.add_argument("-w", "--wordlist", help="Wordlist file")

    # TACTICS
    g_tactics = parser.add_argument_group('🛠️ Tactics')
    g_tactics.add_argument("-t", "--threads", type=int, default=10, help="Thread count")
    g_tactics.add_argument("--delay", type=float, default=0.0, help="Delay in seconds")
    g_tactics.add_argument("--h2", action="store_true", help="Force HTTP/2 (Ferrari Mode)")
    g_tactics.add_argument("--stop", action="store_true", help="🏆 Golden Goal: Stop on first hit")
    g_tactics.add_argument("-H", "--header", action="append", default=[], help="Custom headers")
    
    # OUTPUT
    g_output = parser.add_argument_group('💾 Output')
    g_output.add_argument("-o", "--output", help="Save hits to file")

    return parser

def run_scan(tool_name: str, check_func, args, extra_kwargs: dict = None):
    print(get_banner(tool_name))

    # 1. Config Injection
    if args.threads: config.THREADS = args.threads
    if args.delay: config.DELAY = args.delay
    if args.h2: config.FORCE_HTTP2 = True
    if args.stop: config.STOP_ON_SUCCESS = True

    # 2. Header Parsing
    headers = {}
    for h in args.headers:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = v.strip()
    config.CUSTOM_HEADERS = headers

    # 3. Target Loading
    targets = [""]
    if args.wordlist:
        path = Path(args.wordlist).expanduser().resolve()
        if not path.exists():
            logger.critical(f"❌ Wordlist offside: {path}")
            sys.exit(1)
        # Still reading to memory, but adding error handling
        try:
            targets = [l.strip() for l in path.read_text(errors='ignore').splitlines() if l.strip()]
            logger.info(f"📋 Loaded {len(targets)} payloads.")
        except Exception as e:
            logger.critical(f"❌ Failed to read wordlist: {e}")
            sys.exit(1)

    # 4. Kickoff
    logger.info(f"🚀 Starting {tool_name} → {args.url}")
    
    # Initialize Persistent Requester ONCE
    global_req = Requester()

    hits = engine.run(
        task_function=check_func,
        targets=targets,
        base_url=args.url,
        req=global_req, # Pass the Ferrari
        **(extra_kwargs or {})
    )

    # 5. Victory Lap & Saving
    if hits:
        print("\n" + "═" * 60)
        logger.info(f"🔥 FOUND {len(hits)} HITS")
        
        # Print first few
        for h in hits[:15]:
            print(f"   {h}")
        if len(hits) > 15:
            print(f"   ... and {len(hits)-15} more")
            
        # Save to file if requested
        if args.output:
            try:
                out_path = Path(args.output)
                with out_path.open('w') as f:
                    for h in hits:
                        f.write(f"{h}\n")
                logger.success(f"💾 Saved results to {out_path}")
            except Exception as e:
                logger.error(f"❌ Could not save file: {e}")
                
        print("═" * 60)
    else:
        logger.info("🧱 Clean Sheet. No vulnerabilities found.")
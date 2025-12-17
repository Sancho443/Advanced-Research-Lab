#!/usr/bin/env python3
"""
The Arsenal Base Template — Fixed & Optimized.
"""
import argparse
import sys
import textwrap
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

# ———— ROBUST PATH FIX ————
# Navigate up until we find the 'core' package. 
# This works whether you run from root, templates/, or modules/
current_path = Path(__file__).resolve()
root_path = current_path.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

try:
    from core import engine, logger, config, get_banner, Requester
except ImportError:
    print(f"{Fore.RED}❌ CRITICAL: Could not import 'core'. Are you running this from the right folder?{Style.RESET_ALL}")
    sys.exit(1)

def get_base_parser(tool_name: str) -> argparse.ArgumentParser:
    # Use raw description to preserve the ASCII art spacing
    desc = get_banner(tool_name)
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(desc), 
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

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
    # Kept for legacy compatibility, though tls_client is auto-H2
    g_tactics.add_argument("--h2", action="store_true", help="Force HTTP/2 (Ferrari Mode)") 
    g_tactics.add_argument("--stop", action="store_true", help="🏆 Golden Goal: Stop on first hit")
    
    # ✅ SANCHEZ FIX: dest="headers" ensures args.headers is a list
    g_tactics.add_argument("-H", "--header", action="append", dest="headers", default=[], help="Custom headers")
    
    # OUTPUT
    g_output = parser.add_argument_group('💾 Output')
    g_output.add_argument("-o", "--output", help="Save hits to file")

    return parser

def run_scan(tool_name: str, check_func, args, extra_kwargs: dict = None):
    # Print Banner if not already printed by help
    # print(get_banner(tool_name)) # (Optional, argparse desc might cover it)

    # 1. Config Injection (Tactics Board)
    if args.threads: config.THREADS = args.threads
    if args.delay: config.DELAY = args.delay
    if args.h2: config.FORCE_HTTP2 = True
    if args.stop: config.STOP_ON_SUCCESS = True

    # 2. Header Parsing
    headers = {}
    if args.headers:
        for h in args.headers:
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip()] = v.strip()
    config.CUSTOM_HEADERS = headers

    # 3. Target Loading (The Scouting Report)
    targets = [""] # Default to single shot if no wordlist
    if args.wordlist:
        path = Path(args.wordlist).expanduser().resolve()
        if not path.exists():
            logger.critical(f"❌ Wordlist offside: {path}")
            sys.exit(1)
        
        try:
            # Efficient reading
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                targets = [line.strip() for line in f if line.strip()]
            logger.info(f"📋 Loaded {len(targets)} payloads.")
        except Exception as e:
            logger.critical(f"❌ Failed to read wordlist: {e}")
            sys.exit(1)

    # 4. Kickoff
    logger.info(f"🚀 Starting {tool_name} → {args.url}")
    
    # Initialize Persistent Requester ONCE (The Ferrari)
    global_req = Requester()

    # 🚨 CRITICAL FIX: Pass 'session' as the keyword argument if Engine expects it,
    # or pass it as part of kwargs if Engine unpacks it.
    # Looking at our engine.py, it likely accepts **kwargs and passes them to the task.
    # We will pass 'session=global_req' explicitly so the task_function receives it.
    
    hits = engine.run(
        task_function=check_func,
        targets=targets,
        
        # KEY ARGUMENTS FOR THE TASK FUNCTION:
        base_url=args.url,
        session=global_req, 
        
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
                with out_path.open('w', encoding="utf-8") as f:
                    for h in hits:
                        f.write(f"{h}\n")
                logger.success(f"💾 Saved results to {out_path}")
            except Exception as e:
                logger.error(f"❌ Could not save file: {e}")
                
        print("═" * 60)
    else:
        logger.info("🧱 Clean Sheet. No vulnerabilities found.")
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








    #!/usr/bin/env python3
"""
Module: [TOOL NAME]
Author: Sanchez (The Architect)
Purpose: [WHAT DOES IT HUNT? e.g., SQLi, LFI, Header Analysis]
"""

import argparse
import sys
import os
import urllib.parse
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colors (The Kit)
init(autoreset=True)

# ———— 1. THE CONNECTION (Crucial) ————
# This makes sure we can find the 'core' folder no matter where this script is run.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# ———— 2. THE SQUAD (Imports) ————
from core import engine, logger, config, get_banner, Requester

# ———— 3. THE BRAIN (The Logic) ————
def check_vulnerability(target_input: str, req: Requester, base_url: str, **kwargs) -> str | None:
    """
    The Striker. This function runs inside the threads.
    
    ARGS:
      target_input: The specific item from your wordlist (payload, path, etc).
                    If no wordlist, this might be the URL itself.
      req:          The Global Requester (passed from main to reuse connections).
      base_url:     The target URL from CLI.
      **kwargs:     Extra tactics (headers, cookies, etc).
    """

    # [SANCHEZ TIP 🧠]: 
    # If you are fuzzing, 'target_input' is your payload (e.g., "../etc/passwd").
    # If you are scanning a list of IPs, 'target_input' is the IP.
    
    # A. Build the Target URL
    # Handle the injection marker logic here.
    if "{PAYLOAD}" in base_url:
        # [TACTICAL NOTE]: Always encode payloads if they go into URL params!
        # safe='' encodes everything including / to be safe. Change if needed.
        safe_payload = urllib.parse.quote(target_input, safe='')
        url = base_url.replace("{PAYLOAD}", safe_payload)
    else:
        # Default behavior: Append payload to end
        url = f"{base_url}{target_input}"

    # B. Fire the Shot (Using the Persistent Engine) 🔫
    try:
        # We use the 'req' passed in arguments (The Ferrari).
        # It handles Retries, Timeouts, and HTTP/2 automatically.
        res = req.get(
            url,
            allow_redirects=False # [RED TEAM TIP]: Usually False to spot 301/302 bugs
        )
    except Exception as e:
        # [VAR CHECK]: If it crashes, log debug and keep playing.
        # logger.debug(f"Missed shot on {url}: {e}")
        return None

    if not res:
        return None

    # C. The VAR Review (Detection Logic) 📺
    # This is where the magic happens.
    
    # Example 1: Check Status Code (e.g., Finding Admin Panels)
    # if res.status_code == 200:
    #     return f"{Fore.GREEN}[+] FOUND: {url} ({len(res.content)} bytes)"

    # Example 2: Check Content (e.g., LFI / Error Messages)
    if "root:x:0:0" in res.text: 
        return f"{Fore.GREEN}🔥 VULN FOUND: {url} (LFI Hit!)"
    
    # Example 3: Check Headers (e.g., Missing Security Headers)
    # if "X-Frame-Options" not in res.headers:
    #     return f"{Fore.YELLOW}⚠️  Missing XFO: {url}"

    return None

# ———— 4. THE MANAGER (CLI) ————
def get_arg_parser() -> argparse.ArgumentParser:
    desc = get_banner("[TOOL NAME]") # Put the tool name here
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawTextHelpFormatter)

    # Targeting
    target_group = parser.add_argument_group('🎯 Targeting')
    target_group.add_argument("-u", "--url", required=True, help="Target URL (Use {PAYLOAD} marker if fuzzing)")
    
    # [SANCHEZ TIP 🧠]: Not all tools need a wordlist! 
    # If scanning one target, make this optional with nargs='?' or remove required=True.
    target_group.add_argument("-w", "--wordlist", help="Payload Wordlist (Optional for single-shot tools)")

    # Tactics
    tactics_group = parser.add_argument_group('🛠️  Tactics')
    tactics_group.add_argument("-t", "--threads", type=int, default=10, help="Concurrency level")
    tactics_group.add_argument("--delay", type=float, default=0.0, help="Stealth delay between requests")
    tactics_group.add_argument("--stop", action="store_true", help="🏆 Golden Goal: Stop on first hit")
    
    # [NEW SIGNING]: Force HTTP/2 Support
    tactics_group.add_argument("--h2", action="store_true", help="Force HTTP/2 (Bypass Cloudflare/WAFs)")

    # Headers (The 'dest="headers"' fixes the crash we had earlier!)
    tactics_group.add_argument("-H", "--header", action="append", dest="headers", default=[], help="Custom Headers (e.g. 'Cookie: admin=true')")

    return parser

# ———— 5. THE KICKOFF ————
def main():
    parser = get_arg_parser()
    args = parser.parse_args()
    print(get_banner("[TOOL NAME]"))

    # A. Unlock & Update Config (The New Way) 🔓
    # No more 'object.__setattr__' nonsense. We run this club properly now.
    if args.threads: config.THREADS = args.threads
    if args.delay: config.DELAY = args.delay
    if args.stop: config.STOP_ON_SUCCESS = True
    if args.h2: config.FORCE_HTTP2 = True

    # B. Parse Custom Headers
    # Converts list ["Cookie: a=b", "User-Agent: X"] -> Dict {"Cookie": "a=b", ...}
    headers = {}
    for h in args.headers:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = v.strip()
    config.CUSTOM_HEADERS = headers

    # C. Initialize the Squad (The Global Requester) 🏎️
    # We build it HERE so we can pass it to the threads.
    # This enables Connection Pooling (HTTP/2 Speed).
    logger.info("🔧 Initializing Global Engine...")
    global_req = Requester()

    # D. Load Ammo (Flexible Logic) 🔫
    targets = []
    
    if args.wordlist:
        # Scenario 1: Fuzzing Mode (We have a list)
        path = Path(args.wordlist).expanduser().resolve()
        if not path.exists():
            logger.critical(f"❌ Offside! Wordlist not found: {path}")
            sys.exit(1)
        targets = [line.strip() for line in path.read_text(errors='ignore').splitlines() if line.strip()]
        logger.info(f"📋 Loaded {len(targets)} payloads from {path.name}")
    else:
        # Scenario 2: Sniper Mode (No wordlist, just checking the URL itself)
        # [SANCHEZ TIP]: Useful for checking security headers or a single known vuln.
        logger.info("👻 No wordlist provided. Running in Single-Shot Mode.")
        targets = [""] # Empty payload so f"{base_url}{payload}" just becomes base_url

    if not targets:
        logger.error("❌ No targets to shoot at!")
        sys.exit(1)

    # E. Start the Match ⚽
    logger.info(f"🚀 Kickoff: Scanning {args.url}...")
    
    hits = engine.run(
        task_function=check_vulnerability,
        targets=targets,
        
        # [PASS THE BALL]: We pass arguments to the function here
        base_url=args.url,
        req=global_req,   # <--- Passing the Persistent Client!
        
        desc="Fuzzing" # Name for the progress bar
    )

    # F. Full Time Whistle 🏁
    if hits:
        print()
        logger.info(f"🔥 MATCH FINISHED! Found {len(hits)} hits!")
        for hit in hits:
            # Check if hit is already colored, if not, color it
            msg = hit if isinstance(hit, str) else str(hit)
            print(f"   {msg}")
    else:
        logger.info("🧱 Clean Sheet for the target. No vulns found.")

if __name__ == "__main__":
    main()
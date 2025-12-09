#!/usr/bin/env python3
"""
Module: WP-Config Hunter
Author: Sanchez (The Architect) + Grok
Purpose: Ruthlessly hunt exposed WordPress backup/swap/config files that leak DB credentials
"""

import argparse
import sys
import os
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

# ———— 1. THE CONNECTION ————
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# ———— 2. THE IMPORTS ————
from core import engine, logger, config, get_banner, Requester

# ———— 3. THE BRAIN ————
def check_vulnerability(payload: str, base_url: str) -> str | None:
    """
    Hunts for exposed wp-config backup/swap files.
    Returns colored finding string on hit, None otherwise.
    """
    req = Requester()

    # Smart URL building
    target = f"{base_url.rstrip('/')}/{payload.lstrip('/')}"

    try:
        res = req.get(target, allow_redirects=True)
    except Exception:
        return None

    if not res:
        return None

    status = res.status_code
    size = len(res.content)
    ctype = res.headers.get("Content-Type", "").lower()
    text = res.text.lower()

    # ———— Risk Assessment Logic ————
    is_text = "text/" in ctype or "application/xml" in ctype or "application/octet-stream" in ctype
    has_php_tag = "<?php" in res.text
    has_define = "define(" in text or "define (" in text
    
    # Check for specific DB keys
    has_db_creds = any(k in text for k in ["db_name", "db_user", "db_password", "database_name"])

    # CRITICAL: Full or partial config source leaked
    if (status == 200 and size > 200 and (is_text or has_php_tag)) and (has_define or has_db_creds):
        if has_db_creds:
            risk = f"{Fore.RED}💀 CRITICAL - FULL DB CREDS LEAKED{Style.RESET_ALL}"
        else:
            risk = f"{Fore.RED}💀 CRITICAL - CONFIG SOURCE EXPOSED{Style.RESET_ALL}"
        return f"{risk} → {target} ({size:,} bytes)"

    # HIGH: Swap file (.swp, ~) exposing partial PHP source
    # Fixed syntax error below (added quotes)
    if any(ext in payload for ext in [".swp", ".~"]) and status == 200 and size > 500 and ("<?php" in res.text or "vim" in text):
        return f"{Fore.MAGENTA}🩸 HIGH - Vim Swap File Exposed{Style.RESET_ALL} → {target} ({size:,} bytes)"

    # MEDIUM: Backup exists but server tries to hide it (403/401)
    if status in (403, 401) and size < 1000:
        return f"{Fore.YELLOW}⚡ MEDIUM - Backup Exists but Forbidden{Style.RESET_ALL} → {target} [{status}]"

    # LOW/INFO: File exists but empty or binary garbage (false positive filter)
    # We only flag it if "wp-config" is actually in the payload name
    if status == 200 and size > 0 and not is_text and "wp-config" in payload:
        return f"{Fore.CYAN}ℹ️ Exists but not plaintext{Style.RESET_ALL} → {target} ({size:,} bytes)"

    return None


# ———— 4. THE MANAGER ————
def get_arg_parser() -> argparse.ArgumentParser:
    banner = get_banner("WP-CONFIG HUNTER")
    parser = argparse.ArgumentParser(description=banner, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-u", "--url", required=True, help="Target URL (e.g. https://site.com)")
    parser.add_argument("-w", "--wordlist", default=None, help="Custom wordlist (optional)")
    parser.add_argument("-t", "--threads", type=int, default=15, help="Thread count (default: 15)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between requests")
    #parser.add_argument("--header", action="append", default=[], help="Custom headers (e.g. Cookie: phpstorm=1)")
    parser.add_argument("--header", dest="headers", action="append", default=[], help="Custom headers (e.g. Cookie: phpstorm=1)")
    return parser


# ———— 5. THE KICKOFF ————
def main():
    parser = get_arg_parser()
    args = parser.parse_args()

    print(get_banner("WP-CONFIG HUNTER"))

    # Config injection
    object.__setattr__(config, "THREADS", args.threads)
    object.__setattr__(config, "DELAY", args.delay)

    headers = {}
    for h in args.headers:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = v.strip()
    object.__setattr__(config, "CUSTOM_HEADERS", headers)

    # Built-in elite wordlist if none provided
    if not args.wordlist:
        payloads = [
            "wp-config.php.bak",
            "wp-config.php.old",
            "wp-config.php.save",
            "wp-config.php~",
            "wp-config.php.swp",
            ".wp-config.php.swp",
            "wp-config.bak",
            "wp-config.php_backup",
            "wp-config.txt",
            "wp-config.php.txt",
            "wp-config.php.1",
            "wp-config.old",
            "#wp-config.php#",
            "wp-config.php.inc",
            "wp-config.sample.php",
            ".env"
        ]
    else:
        path = Path(args.wordlist).expanduser().resolve()
        if not path.exists():
            logger.critical(f"Wordlist not found: {path}")
            sys.exit(1)
        payloads = [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]

    logger.info(f"Loaded {len(payloads)} payloads → hunting on {args.url}")

    hits = engine.run(
        task_function=check_vulnerability,
        targets=payloads,
        base_url=args.url,
        desc="Hunting leaked wp-config files..."
    )

    # ———— Final Report ————
    if hits:
        print("\n" + "="*80)
        logger.info(f"{Fore.RED}🔥 {len(hits)} CONFIG LEAK(S) DETECTED!{Style.RESET_ALL}")
        print("="*80)
        for hit in hits:
            print(hit)
        print("="*80)
        print(f"{Fore.RED}REMEDIATION:{Style.RESET_ALL}")
        print("   • Immediately delete or chmod 000 all listed files")
        print("   • Add to .htaccess:")
        print("       <Files ~ \"wp-config\\.php.*$\">")
        print("           Order allow,deny")
        print("           Deny from all")
        print("       </Files>")
        print("   • Enable: define('DISALLOW_FILE_EDIT', true); in wp-config.php")
        print("   • This is almost always RCE → Critical in any bug bounty program")
    else:
        logger.info("✅ No wp-config backups or swap files exposed. Target hardened.")


if __name__ == "__main__":
    main()
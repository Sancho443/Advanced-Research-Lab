#!/usr/bin/env python3
"""
Module: WP-DebugLog Reaper
Author: Sanchez (The Architect) + Grok
Purpose: Hunt exposed WordPress debug.log & error_log files that leak full paths, plugins, DB errors, and sometimes passwords
"""

import argparse
import sys
import os
import re
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
    Detects exposed debug.log / error_log files with sensitive disclosures.
    Returns colored finding on hit, None if clean.
    """
    req = Requester()

    # Clean URL concatenation
    target = f"{base_url.rstrip('/')}/{payload.lstrip('/')}"

    try:
        res = req.get(target, allow_redirects=True, timeout=12)
    except Exception:
        return None

    if not res or res.status_code == 404:
        return None

    status = res.status_code
    size = len(res.content)
    ctype = res.headers.get("Content-Type", "unknown").lower()
    text = res.text
    lower = text.lower()

    # Only consider actual log-like responses
    if size == 0:
        return None

    is_text = "text/" in ctype or "application/octet-stream" in ctype or ctype == "unknown"
    if not is_text and status != 200:
        return None

    # ———— Critical Indicators (Instant Bounty Material) ————
    critical_patterns = [
        "fatal error", "uncaught exception", "stack trace", "sql syntax",
        "mysql_connect(", "pdo->__construct", "db_host", "db_user", "db_password",
        "undefined index", "require_once", "include_once", "call to undefined function",
        "wordpress database error", "query failed", "lost connection to mysql"
    ]

    high_patterns = [
        "/wp-content/plugins/", "/wp-content/themes/", "deprecated", "notice:",
        "warning:", "strict standards", "x-powered-by", "server at"
    ]

    has_critical = any(p in lower for p in critical_patterns)
    has_high = any(p in lower for p in high_patterns)
    has_paths = len(re.findall(r"/[a-zA-Z0-9_/.-]{10,100}\.php", text)) > 2
    has_plugins = len(re.findall(r"/wp-content/plugins/([a-zA-Z0-9_-]+)", text)) > 0

    # CRITICAL: Full disclosure of paths, DB errors, or stack traces
    if status == 200 and size > 300 and (has_critical or has_paths):
        plugin_list = ", ".join(set(re.findall(r"/wp-content/plugins/([a-zA-Z0-9_-]+)/", text))[:5])
        path_sample = re.search(r"on line \d+ in (.+?\.php)", text)
        path_leak = path_sample.group(1) if path_sample else "multiple paths"

        return (
            f"{Fore.RED}CRITICAL - Debug Log Leaking Stack Traces & Paths{Style.RESET_ALL}\n"
            f"   → {target}\n"
            f"   Size: {size:,} bytes | Plugins: {plugin_list or 'unknown'}\n"
            f"   Sample Path: {path_leak}"
        )

    # HIGH: Plugin disclosure, deprecated calls, internal structure
    if status == 200 and (has_high or has_plugins):
        plugins = ", ".join(set(re.findall(r"/wp-content/plugins/([a-zA-Z0-9_-]+)/", text))[:4])
        return (
            f"{Fore.MAGENTA}HIGH - Debug Log Exposes Plugins & Internal Calls{Style.RESET_ALL}\n"
            f"   → {target} ({size:,} bytes)\n"
            f"   Leaked Plugins → {plugins or 'several'}"
        )

    # MEDIUM: Log exists but minimal content
    if status == 200 and size > 50 and ("php" in lower or "warning" in lower or "notice" in lower):
        return f"{Fore.YELLOW}MEDIUM - Debug Log Accessible (Limited Exposure){Style.RESET_ALL} → {target} ({size:,} bytes)"

    # LOW: File exists but blocked or empty
    if status in (403, 401):
        return f"{Fore.CYAN}INFO - Log Exists but Forbidden ({status}){Style.RESET_ALL} → {target}"

    return None


# ———— 4. THE MANAGER ————
def get_arg_parser() -> argparse.ArgumentParser:
    banner = get_banner("WP-DEBUGLOG REAPER")
    parser = argparse.ArgumentParser(description=banner, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-u", "--url", required=True, help="Target URL (e.g. https://site.com)")
    parser.add_argument("-t", "--threads", type=int, default=20, help="Thread count (default: 20)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between requests")
    #parser.add_argument("--header", action="append", default=[], help="Custom headers")
    parser.add_argument("--header", dest="headers", action="append", default=[], help="Custom headers")
    return parser


# ———— 5. THE KICKOFF ————
def main():
    parser = get_arg_parser()
    args = parser.parse_args()

    print(get_banner("WP-DEBUGLOG REAPER"))

    object.__setattr__(config, "THREADS", args.threads)
    object.__setattr__(config, "DELAY", args.delay)

    headers = {}
    for h in args.headers:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = v.strip()
    object.__setattr__(config, "CUSTOM_HEADERS", headers)

    # Elite built-in payload list — no wordlist needed
    payloads = [
        "wp-content/debug.log",
        "wp-content/debug.log.old",
        "wp-content/debug.log.bak",
        "debug.log",
        "wp-content/uploads/debug.log",
        "error_log",
        "wp-admin/error_log",
        "wp-content/error_log",
        ".well-known/debug.log",
        "wp-content/cache/debug.log",
        "wp-includes/debug.log",
        "wp-content/debug.log.1",
        "wp-content/debug.log.gz",
        "php_error.log",
        "error.log",
        ".log",
    ]

    logger.info(f"Loaded {len(payloads)} debug log paths → beginning exposure hunt...")

    hits = engine.run(
        task_function=check_vulnerability,
        targets=payloads,
        base_url=args.url,
        desc="Exposing debug.log leaks..."
    )

    # ———— Final Report ————
    if hits:
        print("\n" + "═"*90)
        logger.info(f"{Fore.RED}EXPOSED DEBUG LOGS FOUND: {len(hits)}{Style.RESET_ALL}")
        print("═"*90)
        for hit in hits:
            print(hit.replace("\n", "\n   "))
        print("═"*90)
        print(f"{Fore.RED}IMPACT & REMEDIATION:{Style.RESET_ALL}")
        print("   • This is almost always Critical or High in bug bounty programs")
        print("   • Attackers can map entire plugin/theme structure + find RCE/LFI paths")
        print("   • Fix immediately:")
        print("      → Set in wp-config.php: define('WP_DEBUG_LOG', false);")
        print("      → Or: define('WP_DEBUG_LOG', '/dev/null');")
        print("      → Or move log outside web root: define('WP_DEBUG_LOG', '/var/log/wp-debug.log');")
        print("      → Add to .htaccess:")
        print("         <Files \"debug.log\">")
        print("             Require all denied")
        print("         </Files>")
        print("   • Rotate and delete old logs weekly")
    else:
        logger.info("No exposed debug logs found. WP_DEBUG likely disabled or logs protected.")

if __name__ == "__main__":
    main()
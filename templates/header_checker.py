#!/usr/bin/env python3
"""
Module: Header Hunter (The Scout) — Final Elite Edition
Purpose: Passive recon. Tech stack, WAFs, missing headers, insecure cookies.
"""
import sys
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

# ———— IMPORT FIX ————
# 1. Add current dir to path (to find base_template)
sys.path.append(str(Path(__file__).resolve().parent))
from base_template import get_base_parser, run_scan

# 2. Add root dir to path (to find core)
sys.path.append(str(Path(__file__).resolve().parents[1]))
from core import logger

def check(target_input: str, base_url: str, req, **kwargs) -> str | None:
    url = base_url
    try:
        # CRITICAL: Do NOT follow redirects — we want original server headers
        res = req.get(url, allow_redirects=False)
        if not res:
            return None

        findings = []
        h = res.headers  # shortcut

        # ———— 1. TECH STACK ENUMERATION ————
        tech_map = {
            "Server": "🖥️  SERVER",
            "X-Powered-By": "⚡ POWERED BY",
            "X-AspNet-Version": "net .NET",
            "X-Generator": "⚙️  CMS",
            "Via": "proxy PROXY",
            "X-Cache": "📦 CDN CACHE",
            "CF-RAY": "☁️  CLOUDFLARE",
            "X-CDN": "📦 CDN",
        }
        for header, label in tech_map.items():
            # Case-insensitive lookup is safer
            # httpx/requests headers are case-insensitive dicts, so regular access works
            if header in h:
                findings.append(f"{Fore.CYAN}{label}: {h[header]}{Style.RESET_ALL}")

        # ———— 2. MISSING SECURITY HEADERS ————
        required = [
            "Strict-Transport-Security",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Content-Security-Policy",
            "Referrer-Policy",
            "Permissions-Policy"
        ]
        # Check keys case-insensitively just to be safe
        keys_lower = [k.lower() for k in h.keys()]
        missing = [name for name in required if name.lower() not in keys_lower]
        
        if missing:
            findings.append(f"{Fore.YELLOW}⚠️  MISSING: {', '.join(missing)}{Style.RESET_ALL}")

        # ———— 3. INSECURE COOKIES ————
        insecure_cookies = []

        # We rely on the CookieJar objects because it parses attributes for us
        for cookie in res.cookies:
            flags = []
            
            # Secure Flag
            if not cookie.secure: 
                flags.append("NO_SECURE")
            
            # HttpOnly Flag (Tricky: 'requests' uses .has_nonstandard_attr, 'httpx' might parse differently)
            # Universal check:
            # In requests: cookie.has_nonstandard_attr('HttpOnly') returns True/False
            # In httpx/standard cookiejar: it might be an attribute
            
            try:
                # Try the standard method first
                if not cookie.has_nonstandard_attr('HttpOnly'):
                    flags.append("NO_HTTPONLY")
            except AttributeError:
                # Fallback for some CookieJar implementations
                # If we can't check, we assume safe to avoid false positives, or check raw header
                pass

            if flags:
                 insecure_cookies.append(f"{cookie.name} → {', '.join(flags)}")

        if insecure_cookies:
            findings.append(f"{Fore.RED}🍪 INSECURE COOKIES:{Style.RESET_ALL}\n   " + "\n   ".join(insecure_cookies))

        # ———— 4. FINAL VERDICT ————
        if findings:
            return f"{Fore.MAGENTA}🔎 RECON COMPLETE → {url}{Style.RESET_ALL}\n " + "\n ".join(findings)

    except Exception as e:
        logger.debug(f"Header check failed: {e}")

    return None


def main():
    parser = get_base_parser("HEADER HUNTER")
    args = parser.parse_args()
    
    # Header Hunter is a Single-Shot tool (usually)
    # But if user passes -w, it will scan a list of URLs
    
    run_scan("HEADER HUNTER", check, args)


if __name__ == "__main__":
    main()
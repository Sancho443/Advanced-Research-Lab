#!/usr/bin/env python3
"""
Module: API Scanner (The Midfield Maestro)
Purpose: Discovery of REST/GraphQL endpoints.
"""
import sys
from pathlib import Path

# ———— ROBUST IMPORT FIX ————
# Navigate up to root (Arsenal folder)
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from templates.base_template import get_base_parser, run_scan
from core import logger

def check(path: str, base_url: str, session, **kwargs) -> str | None:
    """
    Checks if an API endpoint exists.
    """
    # Clean up the URL join to avoid double slashes (unless it's part of the protocol)
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    if path.startswith("/"):
        path = path[1:]
        
    url = f"{base_url}/{path}"
    
    # [TACTIC]: APIs expect JSON. We must dress the part.
    headers = kwargs.get("headers", {}).copy()
    if "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    if "Accept" not in headers:
        headers["Accept"] = "application/json"

    try:
        # We use 'session' because that's what base_template passes
        res = session.get(url, headers=headers, allow_redirects=False)
        
        if not res: return None

        # [VAR CHECK]: Intelligent Detection 🧠
        
        # 1. The Holy Grail (200 OK with JSON)
        is_json = "application/json" in res.headers.get("content-type", "").lower()
        
        if res.status_code == 200:
            if is_json:
                return f"💎 API ENDPOINT: {url} (200 OK + JSON)"
            
            # Check for JSON-like body even if header is wrong
            if res.text.strip().startswith(("{", "[")):
                return f"💎 API ENDPOINT: {url} (200 OK + JSON Body)"
            
            # Swagger/OpenAPI docs
            if "swagger" in res.text.lower() or "openapi" in res.text.lower():
                return f"📜 DOCUMENTATION: {url} (Swagger Found)"

        # 2. The Locked Doors (401/403) -> Means the endpoint EXISTS!
        if res.status_code in [401, 403]:
            # Filter out generic WAF blocks (usually 403 with HTML body)
            # If it returns JSON error (e.g. {"error": "Unauthorized"}), it's a valid API endpoint
            if is_json or res.text.strip().startswith(("{", "[")):
                return f"🔒 PROTECTED API: {url} ({res.status_code})"

        # 3. Method Hints (405) -> "Don't GET, try POST"
        if res.status_code == 405:
            return f"🛑 METHOD NOT ALLOWED: {url} (Try POST?)"

    except Exception:
        pass
    
    return None

def main():
    parser = get_base_parser("API SCANNER")
    args = parser.parse_args()
    
    # Check if wordlist was provided
    if not args.wordlist:
        logger.critical("❌ API Scanning requires a wordlist (-w)!")
        sys.exit(1)
        
    run_scan("API SCANNER", check, args)

if __name__ == "__main__":
    main()
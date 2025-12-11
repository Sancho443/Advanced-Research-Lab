# modules/traversal.py
from core import Requester, logger
import re

def check_traversal(payload: str, base_url: str) -> str | None:
    """
    Elite LFI/RFI Hunter — detects real inclusions with surgical precision.
    Works on real pentests in 2025.
    """
    if "{PAYLOAD}" in base_url:
        target = base_url.replace("{PAYLOAD}", payload)
    else:
        target = f"{base_url.rstrip('/')}/{payload.lstrip('/')}"

    req = Requester()
    try:
        res = req.get(target, allow_redirects=False, timeout=10)
    except:
        return None

    if not res or res.status_code != 200:
        return None

    content = res.text
    clower = content.lower()
    size = len(content)

    # ———— LFI SIGNATURES (Linux) ————
    linux_patterns = [
        "root:x:0:0:", "/bin/bash", "/bin/sh", "daemon:", "www-data",
        "/etc/passwd", "/proc/version", "ubuntu", "debian", "centos"
    ]
    is_linux = any(pat in clower for pat in linux_patterns)

    # ———— LFI SIGNATURES (Windows) ————
    windows_patterns = [
        "c:\\windows", "program files", "boot.ini", "[boot loader]",
        "nt authority\\system", "administrator:"
    ]
    is_windows = any(pat in clower for pat in windows_patterns)

    # ———— RFI (Remote File Inclusion) ————
    # Use your own canary file: http://your-vps.com/canary.txt → contains "RFI_CANARY_2025"
    is_rfi_canary = "RFI_CANARY_2025" in content

    # RFI code execution (data://, php://input)
    is_rfi_exec = any(marker in content for marker in [
        "system_check", "RCE_SUCCESS", "uid=", "gid=", "<?php system(",
        "id\nuid=", "www-data", "root@", "eval-stdin", "base64_decode",  # new gen
        "assert(code)", "gopher://", "php://filter", "convert.iconv"    # new gen
    ])

    # Vulnerable lab / CTF detection
    # ———— PROJECT FILE CHECKS (New) ————
    # Python Source Code (Leaking the app logic)
    # Looks for imports or function definitions
    is_python = "import " in content and ("from " in content or "def " in content or "flask" in content)
    
    # Requirements File (Leaking dependencies)
    # Looks for standard pip format
    is_requirements = "Flask" in content or "Django" in content or "requests==" in content

    # ———— FINAL VERDICT ————
    if is_linux or is_windows or is_rfi_canary or is_rfi_exec or is_python or is_requirements:
        vuln_type = "LFI"
        icon = "File Inclusion"

        if is_windows:
            vuln_type = "LFI (Windows)"
        elif is_linux:
            vuln_type = "LFI (Linux)"
        elif is_rfi_canary:
            vuln_type = "RFI (Canary Hit)"
            icon = "Remote Include"
        elif is_rfi_exec:
            vuln_type = "RFI → RCE!"
            icon = "CODE EXECUTION"
        elif is_python: 
            vuln_type = "Source Code Leak"     # <--- New
        elif is_requirements: 
            vuln_type = "Dependency Leak"

        return f"{icon} [{vuln_type}] → {target} ({size:,} bytes)"

    return None
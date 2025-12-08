# modules/traversal.py
from core import Requester, logger

# 👇 THIS NAME MUST MATCH EXACTLY
def check_traversal(payload, base_url):
    """
    The pure logic. Takes a payload and a URL. Returns the payload if it works.
    """
    # 1. Prepare the Target
    if "{PAYLOAD}" in base_url:
        target = base_url.replace("{PAYLOAD}", payload)
    else:
        target = f"{base_url}{payload}"

    # 2. Fire the Request
    req = Requester()
    res = req.get(target)

    if not res:
        return None

    # 3. Detection Logic (The "Brain")
    # Linux Signatures
    is_linux = "root:x:0:0" in res.text or "bin/bash" in res.text
    
    # Windows Signatures
    is_windows = "[extensions]" in res.text or "fonts" in res.text
    
    # Vulnerable Lab Signature (Specific to our lab.py)
    # Since our lab just dumps the file content, checking for standard file headers works
    is_lab_success = "Module: Vulnerable Lab" in res.text or "flask" in res.text

    if is_linux or is_windows or is_lab_success:
        logger.info(f"🚨 [VULN] {target} | Size: {len(res.text)}b")
        return payload
            
    return None
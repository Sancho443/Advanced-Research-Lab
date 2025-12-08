# modules/ssrf.py
from core import Requester, logger, config
import time
import re

# Enhanced cloud metadata fingerprints (2025 updated)
# We use Compiled Regex for speed (Senior Dev Move)
CLOUD_SIGNATURES = {
    "AWS": [
        r"ami-id", r"instance-id", r"instance-type", r"security-credentials",
        r"latest/meta-data", r"iam/info"
    ],
    "GCP": [
        r"computeMetadata", r"google-compute-engine"
    ],
    "Azure": [
        r"compute", r"network/interface", r"metadata/instance"
    ],
    "DigitalOcean": [
        r"digitalocean", r"droplet", r"v1.json"
    ],
    "Kubernetes": [
        r"kubernetes", r"serviceaccount", r"token", r"ca.crt"
    ],
    "Docker": [
        r"containers", r"docker", r"/var/run/docker.sock"
    ],
    "Internal Service": [
        r"root:x:0:0", r"phpmyadmin", r"dashboard", 
        r"kibana", r"grafana", r"jenkins"
    ]
}

def _detect_cloud_leak(content: str) -> str | None:
    """Return the name of the cloud if metadata is leaked."""
    if not content:
        return None
    
    # Simple string check first (faster than Regex)
    for cloud, patterns in CLOUD_SIGNATURES.items():
        for pattern in patterns:
            # We use regex to be safe, but you could use 'in' for simple strings
            if re.search(pattern, content, re.IGNORECASE):
                return cloud
    return None

def check_ssrf(payload: str, base_url: str) -> str | None:
    """
    The ultimate SSRF hunter.
    Returns a string if vulnerable, None otherwise.
    """
    # 1. Build target URL
    if "{PAYLOAD}" in base_url:
        target = base_url.replace("{PAYLOAD}", payload)
    else:
        # Smart join: handles slash mess
        target = f"{base_url.rstrip('/')}/{payload.lstrip('/')}"

    req = Requester()

    # 2. Fire with timing (The Stopwatch)
    start = time.time()
    res = None
    try:
        # We assume Requester handles the exception, but we wrap it to be safe
        res = req.get(target)
    except Exception:
        pass # Requester logs errors usually
    finally:
        latency = time.time() - start

    # ———— 3. BLIND SSRF CHECK (The Fix) ————
    # If the request timed out (res is None) BUT took > 5 seconds,
    # that usually means we hit a firewalled internal IP.
    if latency > 5.0:
        status = res.status_code if res else "TIMEOUT"
        logger.warning(f"⏳ Slow Response ({latency:.2f}s) → Possible Blind SSRF | {payload} | Status: {status}")
        return f"{payload} (Blind – {latency:.2f}s)"

    # If it was fast but failed/empty, we stop here
    if not res or not res.text:
        return None

    # ———— 4. CLOUD METADATA JACKPOT ————
    cloud = _detect_cloud_leak(res.text)
    if cloud:
        size = len(res.text)
        logger.critical(f"🚨 CLOUD METADATA LEAK DETECTED → {cloud.upper()} ({size} bytes)")
        return f"{payload} → {cloud.upper()} LEAK"

    # ———— 5. PORT SCANNING (Connection Refused) ————
    # "Connection refused" means the server reached the IP, but the port was closed.
    # This PROVES the server is making requests for us.
    if "connection refused" in res.text.lower():
        logger.info(f"⚠️ Port Closed (Connection Refused) → SSRF Confirmed | {payload}")
        return f"{payload} → Port Closed"

    # ———— 6. INTERNAL SERVICE EXPOSED ————
    # We ignore small responses (often empty JSON or 404 pages)
    if res.status_code == 200 and len(res.text) > 80:
        # Noise Filter: Ignore generic HTML/JSON unless it looks interesting
        if any(w in res.text.lower() for w in ["root:", "admin", "config", "private"]):
            logger.info(f"✅ Internal Content? {res.status_code} | {len(res.text)}b | {payload}")
            return f"{payload} → {res.status_code} ({len(res.text)}b)"

    # ———— 7. ERROR LEAKS ————
    # Sometimes 500 errors leak internal IP addresses or hostnames
    if res.status_code == 500 and "10." in res.text or "192.168" in res.text:
        logger.info(f"💀 Internal IP Leak in Error! | {payload}")
        return f"{payload} → Error Leak"

    return None
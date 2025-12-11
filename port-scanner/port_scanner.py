#!/usr/bin/env python3
"""
Module: Origin Port Scanner (The Sentinel)
Author: Sanchez (The Architect)
Purpose: Scans target IPs for open ports/services using the Red Team Arsenal Engine.
"""

import argparse
import sys
import os
import socket
import ipaddress
from typing import Optional
from colorama import Fore, Style, init
from pathlib import Path

# Initialize colors
init(autoreset=True)

# ———— 1. THE CONNECTION ————
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# ———— 2. THE IMPORTS ————
# Note: We won't use Requester here because this is TCP, not HTTP.
from core import engine, logger, config, get_banner

# Service mapping for cleaner output
PORT_SERVICES = {
    21: "FTP", 22: "SSH", 25: "SMTP", 53: "DNS", 80: "HTTP", 443: "HTTPS",
    3306: "MySQL", 2082: "cPanel", 2083: "cPanel-SSL", 8080: "HTTP-Alt"
}

# ———— 3. THE BRAIN (The Logic) ————
def check_port(port_str: str, target_ip: str) -> str | None:
    """
    The Logic Function.
    INPUT: A port number (as string) and the target IP.
    OUTPUT: A formatted string if open, None if closed.
    """
    try:
        port = int(port_str)
    except ValueError:
        return None

    # Service Name Lookup
    service = PORT_SERVICES.get(port, "Unknown")
    
    # A. Fire the Shot (Socket Connect)
    try:
        # We create a raw socket here instead of using Requester
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Pull timeout from global config if available, else default to 1s
        timeout = getattr(config, "TIMEOUT", 1.0)
        sock.settimeout(timeout)
        
        result = sock.connect_ex((target_ip, port))
        
        if result == 0:
            # B. Banner Grab (The Bonus)
            banner = ""
            try:
                # Send a dummy byte to provoke a response (for non-HTTP services)
                # sock.send(b'\n') 
                banner_data = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                if banner_data:
                    banner = f" | Banner: {banner_data[:40]}..."
            except:
                pass # Banner grabbing failed, but port is still open
            
            sock.close()
            
            # C. Return the Victory String
            return f"{Fore.GREEN}[OPEN] Port {port:<5} ({service}){banner}{Style.RESET_ALL}"
            
        sock.close()
    except Exception:
        return None # Network error

    return None

# ———— 4. THE MANAGER (CLI) ————
def get_arg_parser() -> argparse.ArgumentParser:
    desc = get_banner("ORIGIN SCANNER")
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawTextHelpFormatter)

    # Standard Args
    parser.add_argument("-u", "--ip", required=True, help="Target IPv4 Address")
    
    # We allow EITHER a file list (-w) OR a direct string (-p)
    parser.add_argument("-w", "--wordlist", help="File containing list of ports (one per line)")
    parser.add_argument("-p", "--ports", help="Ports to scan (e.g., '80,443' or '8000-8010')")
    
    # Standard Tactics
    parser.add_argument("-t", "--threads", type=int, default=5, help="Threads (Default: 50)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay (sec)")
    # Headers arg kept for template compatibility, though unused in TCP scan
    parser.add_argument("--header", action="append", default=[], help="Unused for Port Scan")

    return parser

# Helper to parse ranges
def parse_port_string(port_arg: str) -> list[str]:
    ports = set()
    parts = port_arg.split(',')
    for part in parts:
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                ports.update(range(start, end + 1))
            except ValueError:
                continue
        else:
            try:
                ports.add(int(part))
            except ValueError:
                continue
    return [str(p) for p in sorted(list(ports))]

# ———— 5. THE KICKOFF ————
def main():
    parser = get_arg_parser()
    args = parser.parse_args()
    print(get_banner("ORIGIN SCANNER"))

    # A. Validate Target IP
    try:
        ipaddress.IPv4Address(args.ip)
    except ipaddress.AddressValueError:
        logger.critical(f"Invalid IP Address: {args.ip}")
        sys.exit(1)

    # B. Configure the Engine
    object.__setattr__(config, "THREADS", args.threads)
    object.__setattr__(config, "DELAY", args.delay)
    # Set a tighter timeout for port scanning vs HTTP scanning
    object.__setattr__(config, "TIMEOUT", 2.0) 

    # C. Load Ammo (Ports)
    payloads = []
    
    # Option 1: Load from file (-w)
    if args.wordlist:
        path = Path(args.wordlist).expanduser().resolve()
        if not path.exists():
            logger.critical(f"Port list not found: {path}")
            sys.exit(1)
        payloads = [line.strip() for line in path.read_text().splitlines() if line.strip().isdigit()]

    # Option 2: Load from string (-p)
    elif args.ports:
        payloads = parse_port_string(args.ports)
    
    # Option 3: Default
    else:
        payloads = [str(p) for p in [21, 22, 25, 53, 80, 443, 3306, 8080, 8443]]
        logger.info("No ports specified. Using default Top 10.")

    if not payloads:
        logger.critical("No valid ports loaded.")
        sys.exit(1)

    # D. Start the Engine
    logger.info(f"Starting Port Scan on {args.ip} with {len(payloads)} ports...")
    
    hits = engine.run(
        task_function=check_port, 
        targets=payloads,
        base_url=args.ip, # Passing IP as 'base_url'
        desc="Scanning Ports..."
    )

    # E. Victory Lap
    if hits:
        print()
        logger.info(f"🔥 FOUND {len(hits)} OPEN PORTS!")
        # Sort logic: Extract port number from the result string to sort numerically if possible
        # Since hits are just strings now, we print them directly.
        for hit in hits:
            print(f"   {hit}")
    else:
        logger.info("✅ No open ports found (Target is locked down).")

if __name__ == "__main__":
    main()
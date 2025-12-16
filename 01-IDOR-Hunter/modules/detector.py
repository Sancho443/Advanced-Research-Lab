#!/usr/bin/env python3
"""
Module: detector.py
Purpose: Discover candidate ID parameters via API-aware crawling + path analysis.
"""
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from typing import List, Tuple, Set, Any
import re
import json

from core import logger
# Assuming Requester is in core/ (Use TYPE_CHECKING to avoid runtime import loops)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.requester import Requester

# Expanded ID indicators (The "Scout Report")
ID_SUFFIXES = ["_id", "id", "uid", "ref", "key", "token", "no", "num", "code", "uuid", "hash"]
ID_EXACT = [
    "file", "document", "doc", "resource", "item", "object",
    "customer", "client", "order", "invoice", "ticket",
    "post", "user", "account", "profile", "session", "member", "group"
]

def is_in_scope(base_url: str, url: str) -> bool:
    """Keep crawling within the same domain."""
    return urlparse(base_url).netloc == urlparse(url).netloc

def is_id_param(name: str) -> bool:
    """Heuristic: does this param name scream 'identifier'?"""
    lower = name.lower()
    return (
        lower == "id" or
        any(lower.endswith(suffix) for suffix in ID_SUFFIXES) or
        lower in ID_EXACT
    )

def is_potential_id_segment(segment: str) -> bool:
    """
    Detect path segments that look like IDs.
    Now supports: Integers, UUIDs, MongoDB ObjectIDs, Base64-like strings.
    """
    # 1. Pure Numeric (1001)
    if segment.isdigit():
        return True
    
    # 2. UUID (Standard)
    if re.match(r'^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$', segment):
        return True
    
    # 3. MongoDB ObjectID (24 hex chars)
    if re.match(r'^[0-9a-fA-F]{24}$', segment):
        return True

    # 4. Short Alphanumeric (YouTube style / Hashids) - e.g. "x7Hz9j"
    # Rule: Mixed case/numbers, no dots/slashes, length 5-30
    if re.match(r'^[a-zA-Z0-9_-]{5,30}$', segment):
        # Filter out common false positives (static words)
        if not any(char.isdigit() for char in segment): 
             # If it has NO numbers, it's likely just a word like "settings" or "profile"
             # Unless it's a known ID param name? No, risky.
             return False 
        return True

    return False

def extract_from_query(url: str) -> List[Tuple[str, str, str]]:
    """Extract ID params from query string."""
    candidates = []
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    
    if not query_params:
        return candidates

    for param, values in query_params.items():
        if not is_id_param(param):
            continue
        original_value = values[0]

        temp_params = query_params.copy()
        temp_params[param] = ["{ID}"]
        new_query = urlencode(temp_params, doseq=True)

        template_url = urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, new_query, parsed.fragment
        ))

        candidates.append((param, template_url, original_value))

    return candidates

def extract_from_path(url: str) -> List[Tuple[str, str, str]]:
    """Detect dynamic ID segments in the URL path."""
    parsed = urlparse(url)
    segments = [s for s in parsed.path.split('/') if s]
    
    candidates = []
    for i, segment in enumerate(segments):
        if not is_potential_id_segment(segment):
            continue
        
        # Heuristic: The parameter name is usually the PREVIOUS segment
        # e.g. /users/123 -> param name is "users"
        param_name = segments[i-1] if i > 0 else "path_id"
        
        # Don't create a candidate if the "param name" looks like an ID too (e.g. /123/456)
        if is_potential_id_segment(param_name):
            param_name = "nested_id"

        new_segments = segments.copy()
        new_segments[i] = "{ID}"
        template_path = "/" + "/".join(new_segments) + ("/" if parsed.path.endswith("/") else "")

        template_url = urlunparse((
            parsed.scheme, parsed.netloc, template_path,
            parsed.params, parsed.query, parsed.fragment
        ))

        candidates.append((f"{param_name}_path", template_url, segment))

    return candidates

def extract_links_from_text(text: str, base_url: str) -> Set[str]:
    """Extract links from HTML, JSON, or plain text."""
    found = set()
    
    # 1. Standard HREF/SRC (HTML)
    found.update(re.findall(r'(?:href|src)=[\'"]?([^\'" >]+)', text))
    
    # 2. JSON values starting with / or http (API responses)
    # Finds "url": "/api/v1/user" or "avatar": "https://..."
    found.update(re.findall(r'[\'"]((?:/|https?://)[^\'"\s]+)[\'"]', text))

    normalized = set()
    for link in found:
        # Clean up
        link = link.strip().replace("\\/", "/") # Handle escaped JSON slashes
        full_link = urljoin(base_url, link)
        normalized.add(full_link)
    
    return normalized

def detect_id_parameters(
    base_url: str,
    req: 'Requester', # Type hint string to avoid circular import
    max_depth: int = 2,
    max_pages: int = 30
) -> List[Tuple[str, str, str]]:
    """
    Crawler to discover endpoints containing potential ID parameters.
    """
    to_visit: List[Tuple[str, int]] = [(base_url, 0)]
    visited: Set[str] = set()
    candidates: Set[Tuple[str, str, str]] = set()
    pages_crawled = 0

    logger.info(f"Starting ID parameter detection on {base_url}")

    while to_visit and pages_crawled < max_pages:
        current_url, depth = to_visit.pop(0)
        clean_url = current_url.split("#")[0]

        if clean_url in visited:
            continue
        visited.add(clean_url)
        pages_crawled += 1

        if depth > max_depth:
            continue

        logger.debug(f"Crawling [Depth {depth}]: {clean_url}")

        # 1. Extract candidates from the URL itself
        for candidate in extract_from_query(clean_url) + extract_from_path(clean_url):
            candidates.add(candidate)

        # 2. Request and Mine for Links
        try:
            res = req.get(clean_url, allow_redirects=True, timeout=10)
            if not res or res.status_code != 200:
                continue
            
            # CHECK: Only parse text-based formats (HTML, JSON, XML, JS)
            ctype = res.headers.get("Content-Type", "").lower()
            if not any(x in ctype for x in ["html", "json", "xml", "javascript", "text"]):
                continue

            # 3. Extract IDs from the RESPONSE BODY (New Feature!)
            # Sometimes APIs return list of objects: [{"id": 101}, {"id": 102}]
            if "json" in ctype:
                try:
                    data = res.json()
                    # A recursive search for keys named "id" could go here
                    # For now, we rely on the link extractor to find URLs in the JSON
                except:
                    pass

            # 4. Extract Links (HTML + JSON aware)
            links = extract_links_from_text(res.text, current_url)
            
            for full_link in links:
                parsed = urlparse(full_link)
                if parsed.scheme not in ("http", "https"):
                    continue

                link_to_queue = full_link.split("#")[0]
                if (is_in_scope(base_url, link_to_queue) and
                        link_to_queue not in visited and
                        link_to_queue not in [u for u, _ in to_visit]):
                    to_visit.append((link_to_queue, depth + 1))

        except Exception as e:
            logger.debug(f"Crawl error on {clean_url}: {e}")

    logger.info(f"Discovery complete: {len(candidates)} unique ID candidate(s).")
    return list(candidates)

if __name__ == "__main__":
    # Test stub
    pass
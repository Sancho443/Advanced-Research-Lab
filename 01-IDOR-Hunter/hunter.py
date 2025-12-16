#!/usr/bin/env python3
"""
IDOR Hunter — VVD Edition (Solid Defense)
Author: Sanchez (The Architect)
Purpose: IDOR hunting with Fuzzy Logic (difflib) and Auto-Refresh
"""
import sys
from pathlib import Path
import json
import requests
from difflib import SequenceMatcher
from typing import List, Tuple, Optional, Dict
from urllib.parse import urljoin
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Adjust path to find your core modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Assuming these exist in your Advanced-Research-Lab
from core import engine, logger, config, get_banner, Requester
from templates.base_template import get_base_parser
from modules.detector import detect_id_parameters
from modules.guesser import generate_id_payloads


Candidate = Tuple[str, str, str]  # (param_name, template_url, original_value)
TestCase = Tuple[str, str, str]   # (template_url, param_name, payload)
Finding = Dict[str, str]


class SessionManager:
    """
    Wrapper around the Core Requester.
    Adds 'Auto-Refresh' logic on top of the standard engine.
    """
    
    def __init__(self, cookies: Dict[str, str], extra_headers: Dict[str, str],
                 refresh_config: Dict):
        
        # 1. Initialize the Central Engine (Handles Proxies, UA, SSL, H2 automatically)
        self.req = Requester()
        
        # 2. Inject the specific 'Match Day' Tactics (Cookies & Headers from CLI)
        self.req.session.cookies.update(cookies)
        self.req.session.headers.update(extra_headers)
        
        self.refresh_config = refresh_config
        self.refreshed = False 

    def _is_unauthenticated(self, response: requests.Response) -> bool:
        """Detect common signs of expired/invalid session."""
        if not response: return True
        if response.status_code in (401, 403):
            return True
        # Check for redirect to login page (302 Found)
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("Location", "").lower()
            if any(path in location for path in ["/login", "/signin", "/auth"]):
                return True
        indicators = ["session expired", "login required", "unauthorized", "please sign in", "you have been logged out"]
        if any(ind in response.text.lower() for ind in indicators):
            # Double check it's not just a blog post about "session expired"
            if "error" in response.text.lower() or "login" in response.text.lower():
                return True
        return False

    def _perform_refresh(self) -> bool:
        """Try keep-alive refresh -> fallback to full login."""
        cfg = self.refresh_config
        if not cfg.get("refresh_url"):
            return False

        try:
            logger.info(f"Attempting session refresh via {cfg['refresh_url']}")
            kwargs = {"timeout": 15}
            if cfg.get("refresh_method", "GET").upper() == "POST" and cfg.get("refresh_data"):
                kwargs["json"] = cfg["refresh_data"]

            # Use the engine for the refresh call too!
            if cfg["refresh_method"].upper() == "POST":
                refresh_res = self.req.post(cfg["refresh_url"], **kwargs)
            else:
                refresh_res = self.req.get(cfg["refresh_url"], **kwargs)

            if refresh_res and refresh_res.status_code in (200, 201, 204):
                logger.info("Session refreshed successfully")
                return True

            # Fallback to full login
            if cfg.get("login_url") and cfg.get("login_data"):
                logger.warning("Keep-alive failed -> trying full re-login")
                login_res = self.req.post(
                    cfg["login_url"],
                    json=cfg["login_data"],
                    timeout=15
                )
                if login_res and login_res.status_code in (200, 302):
                    logger.info("Re-login succeeded")
                    return True
        except Exception as e:
            logger.error(f"Refresh exception: {e}")

        return False

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        The Smart Wrapper:
        1. Calls the Core Requester (Proxies/UA are handled there).
        2. Checks for Auth Failure.
        3. Refreshes and Retries if needed.
        """
        response = self.req.get(url, **kwargs)
        
        if self._is_unauthenticated(response) and not self.refreshed:
            logger.warning(f"Session appears expired for {url}")
            if self._perform_refresh():
                self.refreshed = True
                response = self.req.get(url, **kwargs)  # Retry with refreshed session
            else:
                logger.error("Session refresh failed – continuing...")
        
        return response


def parse_cookies(cookie_input: str) -> Dict[str, str]:
    """Support raw string or Netscape cookies.txt file."""
    cookies = {}
    try:
        path = Path(cookie_input.strip())
        if path.exists():
            with path.open("r") as f:
                for line in f:
                    if line.startswith("#") or not line.strip():
                        continue
                    parts = line.strip().split("\t")
                    if len(parts) >= 7:
                        cookies[parts[-2]] = parts[-1]
            return cookies
    except Exception:
        pass  # Not a file, treat as raw string

    for part in cookie_input.split(";"):
        if "=" in part:
            name, value = part.strip().split("=", 1)
            cookies[name] = value
    return cookies


def get_similarity(a: str, b: str) -> float:
    """Returns a ratio from 0.0 to 1.0 using difflib (The VAR check)."""
    return SequenceMatcher(None, a, b).ratio()


def check_idor(test_case: TestCase, session: SessionManager, 
               baseline_res: requests.Response) -> Optional[Finding]:
    """
    Robust IDOR detection using Fuzzy Logic.
    We compare the test response against the Baseline (your own authorized data).
    """
    template_url, param, payload = test_case
    test_url = template_url.replace("%7BID%7D", payload).replace("{ID}", payload)

    res = session.get(test_url, allow_redirects=False)
    if not res:
        return None

    # 1. Status Code Check (The obvious bypass)
    # If baseline was 403 (forbidden) and this is 200 (OK), that's a goal.
    if res.status_code == 200 and baseline_res.status_code in (401, 403):
        return {
            "type": "IDOR (Bypass)",
            "url": test_url,
            "parameter": param,
            "payload": payload,
            "evidence": f"Status {baseline_res.status_code} -> 200",
            "confidence": "high"
        }

    # 2. Content Analysis (For 200 OK vs 200 OK)
    if res.status_code == 200 and baseline_res.status_code == 200:
        # A. Keyword Filter (Common error messages hidden in 200 OK)
        error_keywords = ["access denied", "forbidden", "unauthorized", "not found", 
                          "invalid", "permission", "record does not exist", "error"]
        if any(kw in res.text.lower() for kw in error_keywords):
            return None

        # B. Exact Match (If it's identical to baseline, we are just viewing our own profile)
        # OR if the server ignores the ID and returns the default page.
        if res.text == baseline_res.text:
            return None

        # C. Fuzzy Matching (The heavy lifter)
        # Compare structural similarity.
        sim_ratio = get_similarity(baseline_res.text, res.text)

        # Logic:
        # > 0.98: It's virtually the same page (likely False Positive or simple reflection).
        # < 0.60: It's totally different (likely a custom 404 page or redirect to home).
        # 0.60 - 0.98: The Structure matches, but content is different. THIS IS THE ZONE.
        
        if 0.60 <= sim_ratio <= 0.98:
            return {
                "type": "IDOR (Content Leak)",
                "url": test_url,
                "parameter": param,
                "payload": payload,
                "evidence": f"Similarity Ratio: {sim_ratio:.2f} (Structure matches, content differs)",
                "confidence": "high"
            }
        
        # Optional: Catch weird outliers if size diff is massive
        if abs(len(res.text) - len(baseline_res.text)) > 500 and sim_ratio < 0.60:
             return {
                "type": "Anomaly (Low Similarity)",
                "url": test_url,
                "parameter": param,
                "payload": payload,
                "evidence": f"Similarity {sim_ratio:.2f} but valid 200 OK",
                "confidence": "low"
            }

    return None


def deduplicate_findings(findings: List[Finding]) -> List[Finding]:
    """Dictionary comprehension to actually remove duplicates."""
    # Key = (URL, Payload) to ensure uniqueness
    unique = {(f["url"], f["payload"]): f for f in findings}
    return list(unique.values())


def main():
    parser = get_base_parser("IDOR HUNTER - VVD Edition")
    parser.add_argument("--cookie", required=True,
                        help="Raw cookies OR path to cookies.txt")
   # parser.add_argument("--header", action="append", default=[],
    #                    help="Extra headers, e.g. 'Authorization: Bearer xyz'")
    parser.add_argument("--refresh-url", help="URL to keep session alive (e.g. /api/me)")
    parser.add_argument("--refresh-method", default="GET", choices=["GET", "POST"])
    parser.add_argument("--refresh-data", help="JSON for POST refresh")
    parser.add_argument("--login-url", help="Fallback full login URL")
    parser.add_argument("--login-data", help="Fallback login JSON")
    parser.add_argument("--baseline-url", help="Explicit own-resource URL (e.g. your own profile)")
    args = parser.parse_args()

    print(get_banner("IDOR HUNTER - VVD Edition"))

    config.THREADS = args.threads or 10
    config.DELAY = args.delay or 0.2
    if args.h2:
        config.FORCE_HTTP2 = True

    # Parse cookies & headers
    cookies = parse_cookies(args.cookie)
    extra_headers = {}
    for h in args.headers:
        if ":" in h:
            k, v = h.split(":", 1)
            extra_headers[k.strip()] = v.strip()

    # Build refresh config
    refresh_config = {}
    if args.refresh_url:
        refresh_config["refresh_url"] = args.refresh_url
        refresh_config["refresh_method"] = args.refresh_method
        if args.refresh_data:
            try:
                refresh_config["refresh_data"] = json.loads(args.refresh_data)
            except json.JSONDecodeError:
                logger.error("Invalid --refresh-data JSON")
                sys.exit(1)
        if args.login_url and args.login_data:
            refresh_config["login_url"] = args.login_url
            try:
                refresh_config["login_data"] = json.loads(args.login_data)
            except json.JSONDecodeError:
                logger.error("Invalid --login-data JSON")
                sys.exit(1)

    session = SessionManager(cookies, extra_headers, refresh_config)

    # Detect ID parameters
    candidates: List[Candidate] = detect_id_parameters(args.url, session.req)
    if not candidates:
        logger.info("No ID parameters detected. (Clean Sheet for the Server)")
        return

    logger.info(f"Found {len(candidates)} candidate parameter(s)")

    # Baseline response (your own resource)
    baseline_url = args.baseline_url or args.url
    logger.info(f"Fetching baseline from: {baseline_url}")
    baseline_res = session.get(baseline_url)
    
    if not baseline_res:
        logger.error("Failed to retrieve baseline. Game Over.")
        return
    logger.info(f"Baseline: {baseline_res.status_code} ({len(baseline_res.text):,} bytes)")

    # Build test cases
    test_cases: List[TestCase] = []
    for param, template_url, orig_val in candidates:
        logger.info(f"Targeting '{param}' (original: {orig_val})")
        payloads = generate_id_payloads(original_value=orig_val)
        for p in payloads:
            if p != orig_val:
                test_cases.append((template_url, param, p))

    logger.info(f"Generated {len(test_cases)} vectors. Kickoff!")

    raw_hits = engine.run(
        task_function=check_idor,
        targets=test_cases,
        session=session,
        baseline_res=baseline_res,
        desc="IDOR Hunt"
    )

    hits = deduplicate_findings(raw_hits)

    if hits:
        report_path = Path("reports/idor_findings.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        json.dump(hits, report_path.open("w"), indent=2)
        logger.success(f"{len(hits)} unique IDORs -> {report_path}")
        for h in hits:
            # Color code confidence
            conf_tag = "[HIGH]" if h['confidence'] == 'high' else "[LOW]"
            logger.info(f"{conf_tag} {h['type']} -> {h['url']} (Sim: {h.get('evidence')})")
    else:
        logger.info("No IDORs found. Defense is parked.")


if __name__ == "__main__":
    main()
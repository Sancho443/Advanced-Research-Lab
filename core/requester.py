#!/usr/bin/env python3
# Module: Requester
# Author: Sanchez (now officially undroppable)
# Handles HTTP, Proxies, User-Agents, Headers automatically.

import random
import time
import urllib3
import requests
from typing import Optional, Dict, Any
from core.config import config
from .logger import logger


# ———— HTTP/2 UPGRADE (2025 EDITION) ————
try:
    import httpx
    from httpx import Response as HttpxResponse
    HTTP2_AVAILABLE = True
    logger.info("HTTP/2 engine loaded → httpx")
except ImportError:
    HTTP2_AVAILABLE = False
    logger.warning("httpx not installed → HTTP/1.1 only (run: pip install 'httpx[http2]')")

# Optional: Allow forcing HTTP/2 via config (for Cloudflare/Akamai bypass)
FORCE_HTTP2 = getattr(config, "FORCE_HTTP2", False)


# Silence SSL warnings only in lab mode
if not config.VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Requester:
    """
    The Midfield Engine v3 — now with total control.
    """

    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.config = config
        
        # ———— SANCHEZ FIX: Persistent HTTP/2 Client ————
        self.h2_client = None
        if HTTP2_AVAILABLE:
            try:
                # 1. Prepare Proxy for HTTPX (It demands a string, not a dict!)
                # httpx >= 0.24.0 uses 'proxy' (singular)
                h2_proxy = config.PROXY_URL if config.USE_PROXY else None

                self.h2_client = httpx.Client(
                    http2=True,
                    verify=config.VERIFY_SSL,
                    proxy=h2_proxy,                # <--- CHANGED FROM proxies=config.proxies
                    follow_redirects=False,
                    timeout=getattr(config, "TIMEOUT", 10),
                    trust_env=False
                )
            except Exception as e:
                # This log will tell us if it crashes again
                logger.warning(f"Could not init HTTP/2 engine: {e}")

    def _rotate_user_agent(self) -> str:
        if not self.config.RANDOM_USER_AGENT:
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        return random.choice(self.DEFAULT_USER_AGENTS)

    def _build_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        # 1. Prepare Base Headers (Without User-Agent first)
        base_headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "DNT": "1",
        }

        # 2. Get the Global Custom Headers (From CLI)
        global_customs = {}
        if hasattr(config, "CUSTOM_HEADERS") and config.CUSTOM_HEADERS:
            global_customs = config.CUSTOM_HEADERS
            logger.debug(f"Injected custom headers: {global_customs.keys()}")

        # 3. Check if User provided a UA (Case Insensitive Check)
        # We look at both global config keys AND local kwargs keys
        all_keys = [k.lower() for k in list(global_customs.keys()) + list(base_headers.keys())]
        
        # If 'user-agent' is NOT in the custom headers, THEN we rotate
        if "user-agent" not in all_keys:
            base_headers["User-Agent"] = self._rotate_user_agent()
        else:
            logger.debug("Custom User-Agent detected. Rotation disabled.")

        # 4. Merge Everything (Custom wins)
        # Apply global config headers first
        if global_customs:
            base_headers.update(global_customs)
        
        # Apply local request overrides last (highest priority)
        if custom_headers:
            base_headers.update(custom_headers)

        return base_headers

    def request(self, method: str, url: str, **kwargs) -> Any:
        # ———— SANCHEZ FIX: READ CONFIG LIVE! ————
        # We ask the config object directly: "Are we forcing H2 right now?"
        should_force_h2 = getattr(config, "FORCE_HTTP2", False)

        # ———— HTTP/2 AUTO-UPGRADE ————
        # Note: We use 'should_force_h2' instead of the global 'FORCE_HTTP2'
        if HTTP2_AVAILABLE and (should_force_h2 or "h2" in url or "cloudflare" in url.lower()):
            #return self._request_httpx(method, url, **kwargs) <--- BAD. Kills the fallback.
            
            # NEW: Try it, but check the result
             response = self._request_httpx(method, url, **kwargs)
             if response is not None:
                 return response
             
             # If response is None, we implicitly "fall through" to the lines below!
             logger.debug("⚠️ H2 failed, switching to HTTP/1.1...")
        
        
        
        # ———— LEGACY LOGIC (HTTP/1.1) ————
        headers = self._build_headers(kwargs.pop("headers", None))
        # Merge config defaults with any local overrides (local wins)
        request_kwargs = self.config.requests_kwargs.copy()
        request_kwargs.update(kwargs)
        if "allow_redirects" in kwargs: 
            request_kwargs["allow_redirects"] = kwargs.pop("allow_redirects")
          

        # Add delay for politeness/stealth
        if self.config.DELAY > 0 and method.upper() != "HEAD":
            time.sleep(self.config.DELAY)

        for attempt in range(self.config.RETRIES + 1):
            try:
                logger.debug(f"[{method.upper()}] {url} (Attempt {attempt + 1})")

                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    **request_kwargs
                )

                # ———— SANCHEZ TACTIC: NO WHISTLE ————
                # We don't raise_for_status(). 
                # 500s/504s are valid responses in hacking!
                
                if response.status_code == 429:
                    logger.warning(f"Rate limited (429) on {url} – backing off...")
                    # We actually want to retry 429s, so we raise an exception to trigger the retry loop
                    raise requests.exceptions.HTTPError(response=response)
                
                # For everything else (200, 404, 500, 504)... JUST RETURN IT.
                if 200 <= response.status_code < 300:
                    logger.info(f"✅ HTTP/1.1 {response.status_code} → {url}")
                elif response.status_code >= 500:
                    # Log 5xx as Warnings (Orange), not Errors (Red)
                    logger.warning(f"⚠️ Server Fumbled (HTTP {response.status_code}) → {url}")
                else:
                    logger.debug(f"🧱 HTTP/1.1 {response.status_code} → {url}")

                return response

                
            

            except requests.exceptions.Timeout:
                logger.error(f"Timeout on {url} (attempt {attempt + 1})")
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection failed to {url}")
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 429:
                    logger.warning(f"Rate limited (429) on {url} – backing off...")
                else:
                    logger.error(f"HTTP error: {e}")
            except Exception as e:
                logger.critical(f"Unexpected error: {e}")
                return None

            # Only sleep if we have retries left
            if attempt < self.config.RETRIES:
                sleep_time = self.config.BACKOFF * (2 ** attempt) + random.uniform(0.1, 1.0)
                logger.debug(f"Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)

        logger.error(f"Gave up on {url} after {self.config.RETRIES + 1} attempts")
        return None

    # Convenience methods
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> Optional[requests.Response]:
        return self.request("POST", url, **kwargs)

    def head(self, url: str, **kwargs) -> Optional[requests.Response]:
        return self.request("HEAD", url, **kwargs)
    
    def _request_httpx(self, method: str, url: str, **kwargs):
        """Uses the persistent HTTP/2 engine."""
        if not self.h2_client:
            return None

        try:
            # 1. Header Logic (Keep your existing logic)
            headers = self._build_headers(kwargs.pop("headers", None))
            
            # 2. Compatibility: HTTPX uses 'follow_redirects', Requests uses 'allow_redirects'
            if "allow_redirects" in kwargs:
                kwargs["follow_redirects"] = kwargs.pop("allow_redirects")

            # 3. Fire the shot using the PERSISTENT client (self.h2_client)
            response = self.h2_client.request(
                method.upper(), 
                url, 
                headers=headers, 
                **kwargs
            )
            
            logger.info(f"⚡ HTTP/2 Success {response.status_code} → {url}")
            return response

        except Exception as e:
            # If H2 fails, return None so the main loop falls back to HTTP/1.1
            logger.debug(f"HTTP/2 miss ({e}), falling back...")
            return None
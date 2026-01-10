#!/usr/bin/env python3
# Module: Requester(Stealth Edition)
# Author: Sanchez (now officially undroppable)
# Power: Impersonates Chrome 120 to bypass Cloudflare/Akamai
import time
import tls_client  # Ensure tls-client is installed
import urllib3
from typing import Optional, Dict, Any
from core.config import config
from .logger import logger



  


# Silence SSL warnings only in lab mode
if not config.VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Requester:
    """
    The Midfield Engine v4 — Stealth Mode.
    Uses tls_client to mimic real browser TLS fingerprints (JA3).
    """



    def __init__(self):
        
        self.config = config
        # Initialize the Stealth Session
        # client_identifier="chrome_120" -> tells the server "I am literally Chrome"
        self.session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True
        )
        
        
        # ———— BRIDGE 1: HTTP/1.1 (Requests) ————
        if config.USE_PROXY:
            proxies = {
                "http": config.PROXY_URL,
                "https": config.PROXY_URL,
            }
            self.session.proxies.update(proxies)
            self.session.verify = False # REQUIRED for Burp

            logger.warning(f"🎭 Stealth Traffic routed via {config.PROXY_URL}")
        # 3. Sync headers
        self._sync_headers()

    def _sync_headers(self):
        """Load headers from config into the session."""
        base_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache"
        }
        
        # Add Custom Headers from Config
        if hasattr(config, "CUSTOM_HEADERS") and config.CUSTOM_HEADERS:
            base_headers.update(config.CUSTOM_HEADERS)

        self.session.headers.update(base_headers)    
        

    def update_cookies(self, cookies: Dict[str, str]):
        """Helper to update cookies since tls_client works slightly differently."""
        self.session.cookies.update(cookies)

    def request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> Any:
        # Add delay for politeness
        if self.config.DELAY > 0:
            time.sleep(self.config.DELAY)

        # Prepare arguments for tls_client
        # ———— TRANSLATION LAYER (Requests -> tls_client) ————
        
        # 1. Handle Timeout (requests='timeout', tls_client='timeout_seconds')
        # We pop 'timeout' from kwargs so it doesn't crash tls_client
        timeout_val = kwargs.pop('timeout', self.config.TIMEOUT)
        
        # 2. Handle Verify (requests='verify', tls_client='insecure_skip_verify')
        verify_val = kwargs.pop('verify', self.config.VERIFY_SSL)
        # Note: tls_client logic is inverted. Verify=False means Insecure=True
        insecure_skip = not verify_val

        # 3. Handle Redirects (requests='allow_redirects', tls_client='follow_redirects')
        allow_redirects = kwargs.pop('allow_redirects', True)

        # 4. Merge Headers (Don't use wsgiref!)
        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)

        for attempt in range(self.config.RETRIES + 1):
            try:
                response = self.session.execute_request(
                    method=method,
                    url=url,
                    headers=req_headers,
                    timeout_seconds=timeout_val,
                    insecure_skip_verify=insecure_skip,
                    allow_redirects=allow_redirects,
                    **kwargs
                )
                
                # Check for WAF blocks (Cloudflare often returns 403 or 429)
                if response.status_code in [403, 429] and "cloudflare" in response.text.lower():
                    logger.critical(f"🛑 WAF Blocked {url} (Status {response.status_code})")
                    
                # Logging
                if 200 <= response.status_code < 300:
                    logger.info(f"✅ [{method}] {response.status_code} → {url}")
                elif response.status_code >= 500:
                    logger.warning(f"⚠️ Server Error {response.status_code} → {url}")
                else:
                    logger.debug(f"🧱 Status {response.status_code} → {url}")

                return response

            
            except Exception as e:
                logger.critical(f"Unexpected error: {e}")
                if attempt < self.config.RETRIES:
                    time.sleep(self.config.BACKOFF)

            
        return None

    # Convenience methods
    def get(self, url: str, **kwargs) -> Any:
        return self.request("GET", url, **kwargs)
    def post(self, url: str, **kwargs) -> Any:
        return self.request("POST", url, **kwargs)
    
    def head(self, url: str, **kwargs) -> Any:
        return self.request("HEAD", url, **kwargs)
#!/usr/bin/env python3
# Module: Requester
# Author: Sanchez (now officially undroppable)

import random
import time
import urllib3
import requests
from typing import Optional, Dict, Any
from core.config import config
from .logger import logger

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

    def request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        headers = self._build_headers(kwargs.pop("headers", None))

        # Merge config defaults with any local overrides (local wins)
        request_kwargs = self.config.requests_kwargs.copy()
        request_kwargs.update(kwargs)

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

                # Don't retry on client errors (except 429 rate limit)
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    logger.warning(f"Client error {response.status_code} on {url}")
                    return response

                response.raise_for_status()
                logger.info(f"Success {response.status_code} → {url}")
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
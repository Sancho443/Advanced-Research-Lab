#!/usr/bin/env python3
# Module: config.py

#!/usr/bin/env python3
"""
Module: Configuration
Author: Sanchez (now with Mikel Arteta-level tactical discipline)
Purpose: Single source of truth. Touch this file → control the entire Arsenal.
"""

import os
from dataclasses import dataclass ,field
from typing import Optional
from typing import Dict, Any
from pathlib import Path
from colorama import Fore, Style, init
import random
# ———— BANNER (Do NOT touch. This is culture.) ————
# ———— BANNER (The Titan) ————
BANNER = r"""
 ██████╗ ███████╗██████╗     ████████╗███████╗ █████╗ ███╗   ███╗
██╔══██╗██╔════╝██╔══██╗    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║
██████╔╝█████╗  ██║  ██║       ██║   █████╗  ███████║██╔████╔██║
██╔══██╗██╔══╝  ██║  ██║       ██║   ██╔══╝  ██╔══██║██║╚██╔╝██║
██║  ██║███████╗██████╔╝       ██║   ███████╗██║  ██║██║ ╚═╝ ██║
╚═╝  ╚═╝╚══════╝╚═════╝        ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝
   ┌─────────────────────────────────────────────────────┐
   │  >> Developer: SANCHEZ                              │
   │  >> Version:  1.0.0                                 │
   │  >> Status:   N/A chill                             │
   │  >> Philosophy: "Build tools, not run them"         │
   └─────────────────────────────────────────────────────┘ """

# ———— ANIME QUOTES (The Vibe) ————
QUOTES = [
    "\"If we don't fight, we can't win. Fight. Fight.\" – Eren Yeager",
    "\"I will keep moving forward, until I destroy my enemies.\" – Eren Yeager",
    "\"The only way to gain freedom is to fight for it.\" – Eren Yeager",
    "\"Dedicate your hearts! (Shinzo wo Sasageyo!)\" – Erwin Smith",
    "\"This world is cruel, but also very beautiful.\" – Mikasa Ackerman"
]

def get_banner(tool_name: str = "Red Team Arsenal") -> str:
    """Helper to generate a consistent, colored banner with a random quote."""
    
    # 1. The Logo (Red)
    logo = f"{Fore.RED}{BANNER}{Style.RESET_ALL}"

    # 3. The Quote (Cyan & Italic if terminal supports it)
    quote = f"{Fore.CYAN}{random.choice(QUOTES)}{Style.RESET_ALL}"
     
     # 2. The Tool Name (Yellow & Bold)
    subtext = f"{Fore.YELLOW}{Style.BRIGHT}:: {tool_name} :: v2.0{Style.RESET_ALL}"
    
    # 4. The Border
    border = f"{Fore.BLACK}{Style.BRIGHT}{'=' * 65}{Style.RESET_ALL}"
    
    return f"\n{logo}\n {quote}\n\n  {subtext}\n \n{border}\n"
@dataclass(frozen=True, slots=True)
class ArsenalConfig:
    """Immutable config with validation. Because mutable globals are for Spurs fans."""

    # ⏱️ Time Management
    TIMEOUT: int = 10
    RETRIES: int = 3
    BACKOFF: float = 1.5

    # ⚡ Performance
    THREADS: int = 10
    DELAY: float = 0.1

    # 🕵️ Stealth & Identity
    RANDOM_USER_AGENT: bool = True
    VERIFY_SSL: bool = False  # WARNING: Only False in labs. Never in prod.

    # 📝 Logging
    LOG_FILE: str = "arsenal.log"

    # 🔌 Proxy
    USE_PROXY: bool = False
    PROXY_URL: str = "http://127.0.0.1:8080"

    # 💉 Header Injection (The new signing)
    # We use default_factory=dict so every instance gets a fresh dictionary
    CUSTOM_HEADERS: Dict[str, str] = field(default_factory=dict)

    CALLBACK_URL: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate everything on creation – no silent failures allowed."""
        if self.TIMEOUT <= 0:
            raise ValueError("TIMEOUT must be positive, you madman")
        if self.RETRIES < 0:
            raise ValueError("RETRIES cannot be negative")
        if self.BACKOFF < 1.0:
            raise ValueError("BACKOFF < 1.0 means we're going backwards in time")
        if self.THREADS < 1:
            raise ValueError("Can't run zero threads. Even Holding needs a job.")
        if self.DELAY < 0:
            raise ValueError("Negative delay? Are we bending space-time now?")
        if self.USE_PROXY and not self.PROXY_URL:
            raise ValueError("USE_PROXY=True but PROXY_URL empty – pick a lane")

    @property
    def proxies(self) -> Dict[str, str] | None:
        """Return proxy dict only if enabled – saves you from Burp 403s"""
        return {"http": self.PROXY_URL, "https": self.PROXY_URL} if self.USE_PROXY else None

    @property
    def requests_kwargs(self) -> Dict[str, Any]:
        """One-liner for requests.get(..., **config.requests_kwargs)"""
        kwargs: Dict[str, Any] = {
            "timeout": self.TIMEOUT,
            "verify": self.VERIFY_SSL,
            "proxies": self.proxies,
        }
        return kwargs

    @property
    def log_file_path(self) -> Path:
        """Always return absolute path – no more 'file not found' tears"""
        return Path.cwd() / self.LOG_FILE


# ———— Load from environment overrides (the pro move) ————
def _load_config() -> ArsenalConfig:
    return ArsenalConfig(
        TIMEOUT=int(os.getenv("ARSENAL_TIMEOUT", "10")),#time taken for the server to respond,,thats 10sec for now
        RETRIES=int(os.getenv("ARSENAL_RETRIES", "3")),#number of times to retry the connection if it fails
        BACKOFF=float(os.getenv("ARSENAL_BACKOFF", "1.5")),#Between those retries, it waits 1.5x longer each time.
        THREADS=int(os.getenv("ARSENAL_THREADS", "10")),
        DELAY=float(os.getenv("ARSENAL_DELAY", "0.1")),#This is the Sleep Time between every single request.configure this so that you don't get banned
        RANDOM_USER_AGENT=os.getenv("ARSENAL_RANDOM_UA", "true").lower() == "true",#Every request wears a different "Jersey." One looks like Chrome on Windows, the next looks like Safari on iPhone. Harder for the ref (WAF) to track you.
        VERIFY_SSL=os.getenv("ARSENAL_VERIFY_SSL", "false").lower() == "true",#In a lab environment, it's common to use self-signed certificates. Setting VERIFY_SSL to false allows you to bypass SSL verification, preventing those annoying certificate warnings.
        LOG_FILE=os.getenv("ARSENAL_LOG_FILE", "arsenal.log"),#This is the filename where the tool saves the receipts.
        USE_PROXY=os.getenv("ARSENAL_USE_PROXY", "false").lower() == "true",
        PROXY_URL=os.getenv("ARSENAL_PROXY", "http://127.0.0.1:8080"),#
    )




# Global config instance – import this everywhere
config = _load_config()
CONFIG = config                     # ← old tools that do "from core import CONFIG" still work
__all__ = ["config", "CONFIG"]      # ← explicit exports = pro move
# Quick sanity check on import
if config.VERIFY_SSL is False and "LAB" not in os.getenv("ENV", "") and "CTF" not in os.getenv("ENV", ""):
    print("⚠️  WARNING: VERIFY_SSL=False outside lab environment. Hope you like MITM attacks.")
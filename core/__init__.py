# core/__init__.py

# Expose the Class, so tools can instantiate their own engines
from .requester import Requester

# Expose the Config dictionary
from .config import CONFIG,BANNER,get_banner

# Expose the Logger (We need to build this next to make this import work!)
from .logger import logger

# Expose the Engine runner
from .engine import engine

# ———— Default shared requester (lazy tools keep working) ————
_default_requester = Requester()
session = _default_requester.session   # ← restores "from core import session"

# Explicit exports – this is how pros do it
globals().update(config.__dict__)
__all__ = [
    "Requester",
    "logger",
    "config",
    "CONFIG",
    "session",
    "engine",
    "BANNER",
    "get_banner"
]

# ← ADD THIS MAGIC LINE
   # ← makes config.TIMEOUT work when doing "from core import config"


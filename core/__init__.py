# core/__init__.py

# Expose the Class, so tools can instantiate their own engines
from .requester import Requester

# Expose the Config dictionary
from .config import CONFIG

# Expose the Logger (We need to build this next to make this import work!)
from .logger import logger

# ———— Default shared requester (lazy tools keep working) ————
_default_requester = Requester()
session = _default_requester.session   # ← restores "from core import session"

# Explicit exports – this is how pros do it
__all__ = [
    "Requester",
    "logger",
    "config",
    "CONFIG",
    "session",
]
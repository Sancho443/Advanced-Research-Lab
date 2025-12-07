#!/usr/bin/env python3
# Module: logger.py
#!/usr/bin/env python3
"""
Module: Logger
Author: Sanchez 
Purpose: Makes the terminal look like the Emirates on a Champions League night
"""

import logging
import sys
from colorama import Fore, Style, init

# Initialise colorama once, globally – let autoreset handle the cleanup
init(autoreset=True)


class ArsenalFormatter(logging.Formatter):
    """
    Because grey logs are for Spurs fans.
    """

    # Clean colour palette
    COLORS = {
        logging.DEBUG: Fore.LIGHTBLACK_EX,      # actually readable now
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    EMOJIS = {
        logging.DEBUG: "🔍",
        logging.INFO: "✅",
        logging.WARNING: "⚠️ ",
        logging.ERROR: "❌",
        logging.CRITICAL: "💀",
    }

    BASE_FORMAT = "%(asctime)s - %(levelname)-8s - %(message)s"
    DATE_FORMAT = "%H:%M:%S"

    def format(self, record):
        # Pull colour & emoji for this level
        color = self.COLORS.get(record.levelno, Fore.WHITE)
        emoji = self.EMOJIS.get(record.levelno, "  ")

        # Build final format string with colour codes
        log_fmt = f"{color}{emoji} {self.BASE_FORMAT}{Style.RESET_ALL}"

        formatter = logging.Formatter(log_fmt, datefmt=self.DATE_FORMAT)
        return formatter.format(record)


def get_logger(name: str = "Sanchez_Arsenal") -> logging.Logger:
    """
    Returns a pre-configured logger so you can just do:
        from logger import logger
    and start flexing immediately.
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers if module is imported multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)  # default to DEBUG, user can raise later
    logger.propagate = False

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(ArsenalFormatter())

    logger.addHandler(ch)
    return logger


# Default instance for lazy people (like me)
logger = get_logger()

logger.success = lambda msg, *args, **kwargs: logger.log(25, msg, *args, **kwargs)  # type: ignore
logger.warning = lambda msg, *args, **kwargs: logger.log(30, msg, *args, **kwargs)  # type: ignore
logger.critical = lambda msg, *args, **kwargs: logger.log(50, msg, *args, **kwargs)  # type: ignore

# Register SUCCESS level so it shows properly
logging.addLevelName(25, "SUCCESS")
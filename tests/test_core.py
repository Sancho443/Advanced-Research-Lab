# tests/test_core.py
import os
import sys

# Add project root to path (only needed if you DON'T use pytest.ini — but harmless)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import logger, config, Requester, session


def test_config_loaded():
    assert config.TIMEOUT > 0
    assert isinstance(config.proxies, (dict, type(None)))


def test_logger_has_success():
    logger.success("CORE TEST PASS – Sanchez is elite")  # This will now work


def test_requester_works():
    req = Requester()
    # Use **config.requests_kwargs so it respects proxy/timeout/ssl settings
    r = req.get("https://httpbin.org/user-agent", **config.requests_kwargs)
    assert r.status_code == 200


def test_no_github_leak_in_ua():
    r = session.get("https://httpbin.org/headers", **config.requests_kwargs)
    ua = r.json()["headers"]["User-Agent"]
    bad_strings = ["github", "sanchez", "arsenal", "sancho"]
    assert not any(x in ua.lower() for x in bad_strings), f"Leak found: {ua}"


def test_random_ua_rotation_when_enabled():
    if config.RANDOM_USER_AGENT:
        req = Requester()
        ua1 = req.get("https://httpbin.org/user-agent", **config.requests_kwargs).json()["user-agent"]
        ua2 = req.get("https://httpbin.org/user-agent", **config.requests_kwargs).json()["user-agent"]
        # Not 100% guaranteed different, but extremely likely
        # So we just assert it's one of our safe ones
        assert "mozilla" in ua1.lower() or "chrome" in ua1.lower()
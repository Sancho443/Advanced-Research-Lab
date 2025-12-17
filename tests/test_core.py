#!/usr/bin/env python3
"""
Test Suite: The Backbone Fitness Test
Author: Sanchez (QA Division)
Run with: pytest tests/test_core.py -v
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# ———— PATH HACK ————
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core.config import config
from core.requester import Requester
from core.engine import engine

# ———— 1. CONFIG TESTS (The Brain) ————
def test_config_is_mutable():
    """Verify we can actually change tactics mid-game."""
    original_threads = config.THREADS
    
    # Try to change it
    config.THREADS = 99
    assert config.THREADS == 99
    
    # Reset it
    config.THREADS = original_threads

def test_config_defaults():
    """Verify the default tactics are sane."""
    assert config.TIMEOUT > 0
    assert config.RETRIES >= 0
    # We removed FORCE_HTTP2 because tls_client handles it automatically
    # Let's check SSL instead
    assert hasattr(config, "VERIFY_SSL")

# ———— 2. REQUESTER TESTS (The Midfield) ————

# 🚨 KEY CHANGE: We mock tls_client, NOT requests/httpx
@patch("core.requester.tls_client.Session")
def test_requester_initialization(mock_tls_session):
    """Verify the Stealth Engine starts with Chrome 120 fingerprint."""
    # 1. Init
    req = Requester()
    
    # 2. Assert the Session was created with the right disguise
    mock_tls_session.assert_called_with(
        client_identifier="chrome_120",
        random_tls_extension_order=True
    )
    # Check that our session attribute is actually the mock
    assert req.session == mock_tls_session.return_value

@patch("core.requester.tls_client.Session")
def test_requester_execution_flow(mock_session_cls):
    """Test that req.get() correctly calls session.execute_request()."""
    # Setup the Mock
    mock_instance = mock_session_cls.return_value
    
    # Create a fake response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_instance.execute_request.return_value = mock_response

    # Initialize
    req = Requester()
    
    # Fire a shot
    url = "https://example.com"
    req.get(url, timeout=5)
    
    # Verify the Translation Layer worked:
    # We passed 'timeout=5', but it should call with 'timeout_seconds=5'
    mock_instance.execute_request.assert_called_once()
    
    call_kwargs = mock_instance.execute_request.call_args[1]
    
    # Check assertions
    assert call_kwargs['method'] == "GET"
    assert call_kwargs['url'] == url
    assert call_kwargs['timeout_seconds'] == 5  # <--- vital check
    assert 'timeout' not in call_kwargs        # <--- ensures we popped the bad arg

# ———— 3. ENGINE TESTS (The Legs) ————

def dummy_task(target, **kwargs):
    """A dummy striker function."""
    return f"Hit: {target}"

def test_engine_threading():
    """Verify the engine actually runs tasks and returns results."""
    targets = ["A", "B", "C"]
    
    # The engine is generic, so it doesn't care about tls_client details
    results = engine.run(
        task_function=dummy_task,
        targets=targets,
        session=None, # Mock/None is fine for dummy task
        desc="Testing Engine"
    )
    
    assert len(results) == 3
    assert "Hit: A" in results
    assert "Hit: B" in results
    assert "Hit: C" in results

def test_engine_golden_goal():
    """Verify the Golden Goal rule stops the match."""
    # Setup
    config.STOP_ON_SUCCESS = True
    targets = range(100) # 100 targets
    
    # This task always returns a "Goal"
    def scoring_task(t, **kwargs):
        return "GOAL"
    
    results = engine.run(
        task_function=scoring_task,
        targets=targets,
        session=None,
        desc="Golden Goal Test"
    )
    
    # It should NOT process all 100. It should stop early.
    assert len(results) < 100 
    
    # Reset config
    config.STOP_ON_SUCCESS = False
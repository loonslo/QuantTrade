# coding=utf-8
"""
Pytest fixtures and shared utilities for QuantTrade tests.
"""
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory and change to it, cleanup after."""
    original = os.getcwd()
    tmp = tempfile.mkdtemp()
    os.chdir(tmp)
    yield Path(tmp)
    os.chdir(original)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def clean_env():
    """Temporarily clear QuantTrade-related env vars."""
    env_keys = [
        'BINANCE_API_KEY', 'BINANCE_SECRET',
        'ENV', 'APP_ENV', 'PROXY_PORT', 'PROXIES', 'SANDBOX',
    ]
    originals = {k: os.environ.pop(k, None) for k in env_keys}
    yield
    # restore
    for k, v in originals.items():
        if v is not None:
            os.environ[k] = v
        else:
            os.environ.pop(k, None)

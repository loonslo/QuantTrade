# coding=utf-8
"""
Tests for key_manager.py – interactive key management CLI.
External dependencies (SecureConfig, ccxt) are mocked.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module to test (functions)
import importlib.util
spec = importlib.util.spec_from_file_location(
    'key_manager', Path(__file__).parent.parent / 'key_manager.py'
)
key_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(key_manager)


class TestSaveCredentialsInteractive:
    """Tests for save_credentials_interactive."""

    @patch('key_manager.SecureConfig')
    @patch('key_manager.getpass.getpass', side_effect=['test_api_key', 'test_secret'])
    @patch('builtins.input', return_value='1')
    def test_save_cred_interactive_success(self, mock_input, mock_getpass, mock_secure):
        """Verify save + validate flow when credentials are valid."""
        mock_cfg = MagicMock()
        mock_cfg.validate_credentials.return_value = True
        mock_secure.return_value = mock_cfg

        result = key_manager.save_credentials_interactive()

        assert result is True
        mock_cfg.save_credentials.assert_called_once_with('test_api_key', 'test_secret')
        mock_cfg.validate_credentials.assert_called_once()

    @patch('key_manager.SecureConfig')
    @patch('key_manager.getpass.getpass', side_effect=['test_api_key', 'test_secret'])
    @patch('builtins.input', return_value='2')
    def test_save_cred_interactive_with_env_selection(self, mock_input, mock_getpass, mock_secure):
        """Test that environment selection maps correctly."""
        mock_cfg = MagicMock()
        mock_cfg.validate_credentials.return_value = True
        mock_secure.return_value = mock_cfg

        key_manager.save_credentials_interactive()

        mock_secure.assert_called_once_with(env='test')

    @patch('key_manager.SecureConfig')
    @patch('key_manager.getpass.getpass', side_effect=['', ''])
    @patch('builtins.input', return_value='1')
    def test_save_cred_interactive_fails_on_empty_key(self, mock_input, mock_getpass, mock_secure):
        """Empty API key/secret should return False without calling SecureConfig."""
        result = key_manager.save_credentials_interactive()
        assert result is False
        mock_secure.assert_not_called()

    @patch('key_manager.SecureConfig')
    @patch('key_manager.getpass.getpass', side_effect=['test_api_key', 'test_secret'])
    @patch('builtins.input', return_value='1')
    def test_save_cred_interactive_fails_on_validation_error(self, mock_input, mock_getpass, mock_secure):
        """When validate_credentials returns False, credentials should be cleared."""
        mock_cfg = MagicMock()
        mock_cfg.validate_credentials.return_value = False
        mock_secure.return_value = mock_cfg

        result = key_manager.save_credentials_interactive()

        assert result is False
        mock_cfg.clear_credentials.assert_called_once()

    @patch('key_manager.SecureConfig')
    @patch('key_manager.getpass.getpass', side_effect=['test_api_key', 'test_secret'])
    @patch('builtins.input', return_value='1')
    def test_save_cred_interactive_handles_exception(self, mock_input, mock_getpass, mock_secure):
        """Exceptions during save should return False."""
        mock_secure.side_effect = Exception('Disk full')

        result = key_manager.save_credentials_interactive()
        assert result is False


class TestValidateCredentials:
    """Tests for validate_credentials function."""

    @patch('key_manager.SecureConfig')
    def test_validate_returns_true_when_valid(self, mock_secure):
        mock_cfg = MagicMock()
        mock_cfg.validate_credentials.return_value = True
        mock_secure.return_value = mock_cfg

        result = key_manager.validate_credentials()
        assert result is True

    @patch('key_manager.SecureConfig')
    def test_validate_returns_false_when_invalid(self, mock_secure):
        mock_cfg = MagicMock()
        mock_cfg.validate_credentials.return_value = False
        mock_secure.return_value = mock_cfg

        result = key_manager.validate_credentials()
        assert result is False

    @patch('key_manager.SecureConfig')
    def test_validate_returns_false_on_exception(self, mock_secure):
        mock_secure.side_effect = Exception('Config error')

        result = key_manager.validate_credentials()
        assert result is False


class TestClearCredentials:
    """Tests for clear_credentials function."""

    @patch('builtins.input', return_value='y')
    @patch('key_manager.SecureConfig')
    def test_clear_returns_true_on_confirm(self, mock_secure, mock_input):
        mock_cfg = MagicMock()
        mock_secure.return_value = mock_cfg

        result = key_manager.clear_credentials()
        assert result is True
        mock_cfg.clear_credentials.assert_called_once()

    @patch('builtins.input', return_value='n')
    @patch('key_manager.SecureConfig')
    def test_clear_returns_false_on_cancel(self, mock_secure, mock_input):
        result = key_manager.clear_credentials()
        assert result is False
        mock_secure.assert_not_called()

    @patch('builtins.input', return_value='Y')
    @patch('key_manager.SecureConfig')
    def test_clear_is_case_insensitive(self, mock_secure, mock_input):
        result = key_manager.clear_credentials()
        assert result is True

    @patch('builtins.input', return_value='y')
    @patch('key_manager.SecureConfig')
    def test_clear_handles_exception(self, mock_secure, mock_input):
        mock_secure.side_effect = Exception('Error')

        result = key_manager.clear_credentials()
        assert result is False


class TestShowStatus:
    """Tests for show_status function."""

    @patch.dict(os.environ, {'BINANCE_API_KEY': 'env_key', 'BINANCE_SECRET': 'env_secret'})
    @patch('key_manager.SecureConfig')
    def test_show_status_reports_env_vars(self, mock_secure):
        mock_cfg = MagicMock()
        mock_cfg.validate_credentials.return_value = True
        mock_secure.return_value = mock_cfg

        # Should not raise
        key_manager.show_status()

    @patch('key_manager.SecureConfig')
    def test_show_status_reports_missing_keys(self, mock_secure):
        mock_cfg = MagicMock()
        mock_cfg.validate_credentials.side_effect = Exception('fail')
        mock_secure.return_value = mock_cfg

        # Should not raise
        key_manager.show_status()

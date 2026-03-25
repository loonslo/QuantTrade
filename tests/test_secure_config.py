# coding=utf-8
"""
Tests for config/secure.py – SecureConfig class.
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.secure import SecureConfig


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _make_secure_config(temp_dir, env=None, env_vars=None):
    """Factory that creates SecureConfig isolated in temp_dir."""
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    if env_vars:
        for k, v in env_vars.items():
            os.environ[k] = v
    try:
        cfg = SecureConfig(env=env)
        return cfg
    finally:
        os.chdir(original_cwd)
        if env_vars:
            for k in env_vars:
                os.environ.pop(k, None)


# ------------------------------------------------------------------
# SecureConfig basics
# ------------------------------------------------------------------
class TestSecureConfigInit:
    """Basic initialization tests."""

    def test_init_creates_env_file_if_missing(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        assert Path('.env').exists()

    def test_init_creates_config_json_if_missing(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        assert Path('config.json').exists()

    def test_env_defaults_to_development(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        assert cfg.env == 'development'

    def test_env_can_be_set_explicitly(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir, env='production')
        assert cfg.env == 'production'

    def test_proxy_port_defaults_to_6823(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        assert cfg.proxy_port == 6823

    def test_proxy_port_from_env_var(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir, env_vars={'PROXY_PORT': '9999'})
        assert cfg.proxy_port == 9999


# ------------------------------------------------------------------
# Configuration loading
# ------------------------------------------------------------------
class TestSecureConfigLoadConfig:
    """Tests for _load_config and related methods."""

    def test_load_config_returns_dict(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        assert isinstance(cfg.config, dict)

    def test_load_config_contains_expected_keys(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        assert 'timeout' in cfg.config
        assert 'enableRateLimit' in cfg.config
        assert 'proxies' in cfg.config

    def test_load_config_timeout_from_config_json(self, temp_dir, clean_env):
        Path('config.json').write_text(
            json.dumps({'timeout': 5000}), encoding='utf-8'
        )
        cfg = _make_secure_config(temp_dir)
        assert cfg.config['timeout'] == 5000

    def test_load_config_env_overrides_config_json(self, temp_dir, clean_env):
        Path('config.json').write_text(
            json.dumps({'timeout': 5000}), encoding='utf-8'
        )
        cfg = _make_secure_config(temp_dir, env_vars={'timeout': '3000'})
        # Note: _get_from_env_or_file for timeout looks up os.getenv('timeout')
        # directly, not 'TIMEOUT'. Let's check the actual behaviour...
        # Actually looking at the code: override('timeout') calls
        # _get_from_env_or_file('timeout') which checks os.getenv('timeout')
        # So we need to set 'timeout' in env, not 'TIMEOUT'.
        assert cfg.config['timeout'] == 3000


# ------------------------------------------------------------------
# Encryption / decryption
# ------------------------------------------------------------------
class TestSecureConfigEncryption:
    """Tests for _encrypt_data / _decrypt_data."""

    def test_encrypt_decrypt_roundtrip(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        original = 'my_secret_data_123'
        encrypted = cfg._encrypt_data(original)
        decrypted = cfg._decrypt_data(encrypted)
        assert decrypted == original
        assert encrypted != original

    def test_encrypt_produces_different_output_each_time(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        data = 'test_data'
        e1 = cfg._encrypt_data(data)
        e2 = cfg._encrypt_data(data)
        # Fernet uses a timestamp, so same data encrypts differently
        assert e1 != e2

    def test_different_keys_produce_different_ciphertext(self, temp_dir, clean_env):
        # Two different configs have different keys
        cfg1 = _make_secure_config(temp_dir)
        key_file = Path('.secret_key')
        key1 = key_file.read_bytes()

        # Remove key so a new one is generated
        key_file.unlink()
        cfg2 = _make_secure_config(temp_dir)
        key2 = key_file.read_bytes()

        assert key1 != key2
        # And they can't decrypt each other's data
        with pytest.raises(Exception):  # Fernet decryption fails
            cfg2._decrypt_data(cfg1._encrypt_data('cross'))


# ------------------------------------------------------------------
# Encrypted config save / load
# ------------------------------------------------------------------
class TestSecureConfigEncryptedStorage:
    """Tests for _save_encrypted_config / _load_encrypted_config."""

    def test_save_and_load_roundtrip(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        data = {'apiKey': 'key123', 'secret': 'sec456'}
        cfg._save_encrypted_config(data)

        loaded = cfg._load_encrypted_config()
        assert loaded == data

    def test_load_encrypted_config_returns_none_when_file_missing(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        assert cfg._load_encrypted_config() is None


# ------------------------------------------------------------------
# Credentials management
# ------------------------------------------------------------------
class TestSecureConfigCredentials:
    """Tests for save_credentials / clear_credentials / _get_api_credentials."""

    def test_save_and_get_credentials(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        cfg.save_credentials('my_api_key', 'my_secret')
        creds = cfg._get_api_credentials()
        assert creds['apiKey'] == 'my_api_key'
        assert creds['secret'] == 'my_secret'

    def test_clear_credentials_removes_files(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        cfg.save_credentials('key', 'secret')
        assert Path('.encrypted_config').exists()
        assert Path('.secret_key').exists()

        cfg.clear_credentials()

        assert not Path('.encrypted_config').exists()
        assert not Path('.secret_key').exists()

    def test_get_api_credentials_prefers_env_over_encrypted(self, temp_dir, clean_env):
        cfg = _make_secure_config(
            temp_dir,
            env_vars={'BINANCE_API_KEY': 'env_key', 'BINANCE_SECRET': 'env_sec'}
        )
        cfg.save_credentials('saved_key', 'saved_secret')
        creds = cfg._get_api_credentials()
        assert creds['apiKey'] == 'env_key'
        assert creds['secret'] == 'env_sec'

    def test_get_api_credentials_falls_back_to_encrypted(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        cfg.save_credentials('saved_key', 'saved_secret')
        creds = cfg._get_api_credentials()
        assert creds['apiKey'] == 'saved_key'
        assert creds['secret'] == 'saved_secret'

    def test_get_api_credentials_returns_none_in_production_without_key(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir, env='production')
        # No env vars, no encrypted config
        creds = cfg._get_api_credentials()
        assert creds is None


# ------------------------------------------------------------------
# Public config methods
# ------------------------------------------------------------------
class TestSecureConfigPublicMethods:
    """Tests for get_binance_config / get_public_config."""

    def test_get_public_config_returns_dict(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        public = cfg.get_public_config()
        assert isinstance(public, dict)

    def test_get_binance_config_raises_without_credentials(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir, env='production')
        # No env vars, no encrypted config
        with pytest.raises(ValueError, match='未找到API密钥'):
            cfg.get_binance_config()

    def test_get_binance_config_returns_credentials_when_saved(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir, env='production')
        cfg.save_credentials('prod_key', 'prod_secret')
        config = cfg.get_binance_config()
        assert config['apiKey'] == 'prod_key'
        assert config['secret'] == 'prod_secret'

    def test_get_binance_config_includes_public_settings(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        cfg.save_credentials('key', 'secret')
        config = cfg.get_binance_config()
        assert 'timeout' in config
        assert 'proxies' in config


# ------------------------------------------------------------------
# validate_credentials (mocked ccxt)
# ------------------------------------------------------------------
class TestSecureConfigValidateCredentials:
    """Tests for validate_credentials with mocked external calls."""

    def test_validate_credentials_returns_true_on_success(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        cfg.save_credentials('test_key', 'test_secret')

        mock_exchange = MagicMock()
        mock_exchange.fetch_balance.return_value = {'total': {}}

        with patch('config.secure.ccxt') as mock_ccxt:
            mock_ccxt.binance.return_value = mock_exchange
            result = cfg.validate_credentials()
            assert result is True
            mock_exchange.fetch_balance.assert_called_once()

    def test_validate_credentials_returns_false_on_exception(self, temp_dir, clean_env):
        cfg = _make_secure_config(temp_dir)
        cfg.save_credentials('bad_key', 'bad_secret')

        with patch('config.secure.ccxt') as mock_ccxt:
            mock_ccxt.binance.side_effect = Exception('Connection refused')
            result = cfg.validate_credentials()
            assert result is False

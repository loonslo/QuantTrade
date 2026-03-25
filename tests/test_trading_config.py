# coding=utf-8
"""
Tests for trading_config.py – TradingConfig class.
"""
import json
import os
from unittest.mock import patch, mock_open

import pytest

# Ensure imports work from the project root
import sys
sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))

from config.trading import TradingConfig


class TestTradingConfigDefaults:
    """Tests for default configuration values."""

    def test_default_test_mode_is_true(self):
        cfg = TradingConfig(config_file='nonexistent_trading_config.json')
        assert cfg.is_test_mode() is True

    def test_default_symbol(self):
        cfg = TradingConfig(config_file='nonexistent_trading_config.json')
        assert cfg.config.get('symbol') == 'BTC/USDT'

    def test_default_strategy(self):
        cfg = TradingConfig(config_file='nonexistent_trading_config.json')
        assert cfg.config.get('strategy') == 'mean_reversion'

    def test_default_initial_capital(self):
        cfg = TradingConfig(config_file='nonexistent_trading_config.json')
        assert cfg.config.get('initial_capital') == 10000

    def test_default_check_interval(self):
        cfg = TradingConfig(config_file='nonexistent_trading_config.json')
        assert cfg.config.get('check_interval') == 60

    def test_default_risk_management(self):
        cfg = TradingConfig(config_file='nonexistent_trading_config.json')
        assert cfg.config.get('max_position_size') == 0.1
        assert cfg.config.get('max_daily_loss') == 0.05

    def test_default_commission_rate(self):
        cfg = TradingConfig(config_file='nonexistent_trading_config.json')
        assert cfg.config.get('commission_rate') == 0.001


class TestTradingConfigGetSet:
    """Tests for get/set methods."""

    def test_get_returns_value(self):
        cfg = TradingConfig(config_file='nonexistent.json')
        assert cfg.get('symbol') == 'BTC/USDT'

    def test_get_with_default(self):
        cfg = TradingConfig(config_file='nonexistent.json')
        assert cfg.get('nonexistent_key', 'default_val') == 'default_val'

    def test_get_returns_none_for_missing_key(self):
        cfg = TradingConfig(config_file='nonexistent.json')
        assert cfg.get('nonexistent_key') is None

    def test_set_updates_config(self):
        cfg = TradingConfig(config_file='nonexistent.json')
        cfg.set('symbol', 'ETH/USDT')
        assert cfg.config['symbol'] == 'ETH/USDT'


class TestTradingConfigFileOperations:
    """Tests for save/load from file."""

    def test_save_and_load_custom_config(self, temp_dir):
        cfg = TradingConfig(config_file=str(temp_dir / 'saved_trading.json'))
        cfg.set('symbol', 'ETH/USDT')
        cfg.set('initial_capital', 50000)
        cfg.save_config()

        # Load in a new instance
        cfg2 = TradingConfig(config_file=str(temp_dir / 'saved_trading.json'))
        assert cfg2.get('symbol') == 'ETH/USDT'
        assert cfg2.get('initial_capital') == 50000

    def test_load_config_merges_with_defaults(self, temp_dir):
        # Write a partial config file
        partial = {'symbol': 'DOGE/USDT', 'initial_capital': 999}
        path = temp_dir / 'partial.json'
        path.write_text(json.dumps(partial), encoding='utf-8')

        cfg = TradingConfig(config_file=str(path))
        # User value should override default
        assert cfg.get('symbol') == 'DOGE/USDT'
        # Default should still be present
        assert cfg.get('strategy') == 'mean_reversion'
        assert cfg.get('initial_capital') == 999


class TestTradingConfigValidation:
    """Tests for validate_config method."""

    def test_validate_passes_with_defaults(self):
        cfg = TradingConfig(config_file='nonexistent.json')
        assert cfg.validate_config() is True

    def test_validate_fails_for_invalid_max_position(self, temp_dir):
        cfg = TradingConfig(config_file=str(temp_dir / 'invalid.json'))
        cfg.set('max_position_size', 1.5)  # > 1
        assert cfg.validate_config() is False

    def test_validate_fails_for_negative_max_position(self, temp_dir):
        cfg = TradingConfig(config_file=str(temp_dir / 'invalid2.json'))
        cfg.set('max_position_size', -0.1)
        assert cfg.validate_config() is False

    def test_validate_fails_for_invalid_max_daily_loss(self, temp_dir):
        cfg = TradingConfig(config_file=str(temp_dir / 'invalid3.json'))
        cfg.set('max_daily_loss', 2.0)
        assert cfg.validate_config() is False

    def test_validate_fails_for_negative_commission(self, temp_dir):
        cfg = TradingConfig(config_file=str(temp_dir / 'invalid4.json'))
        cfg.set('commission_rate', -0.01)
        assert cfg.validate_config() is False

    def test_validate_fails_for_production_without_api_key(self, temp_dir):
        cfg = TradingConfig(config_file=str(temp_dir / 'prod.json'))
        cfg.set('test_mode', False)
        cfg.set('api_key', '')
        cfg.set('api_secret', '')
        # Even without env vars, validation should fail
        assert cfg.validate_config() is False


class TestTradingConfigApiCredentials:
    """Tests for get_api_credentials method."""

    def test_get_credentials_returns_tuple(self):
        cfg = TradingConfig(config_file='nonexistent.json')
        api_key, api_secret = cfg.get_api_credentials()
        assert isinstance(api_key, str)
        assert isinstance(api_secret, str)

    def test_get_credentials_from_config(self, temp_dir):
        cfg = TradingConfig(config_file=str(temp_dir / 'creds.json'))
        cfg.set('api_key', 'test_key_123')
        cfg.set('api_secret', 'test_secret_456')
        api_key, api_secret = cfg.get_api_credentials()
        assert api_key == 'test_key_123'
        assert api_secret == 'test_secret_456'

    def test_get_credentials_from_env_var(self, clean_env):
        os.environ['BINANCE_API_KEY'] = 'env_key'
        os.environ['BINANCE_SECRET'] = 'env_secret'
        cfg = TradingConfig(config_file='nonexistent.json')
        api_key, api_secret = cfg.get_api_credentials()
        assert api_key == 'env_key'
        assert api_secret == 'env_secret'


class TestTradingConfigIsTestMode:
    """Tests for is_test_mode method."""

    def test_is_test_mode_true_by_default(self):
        cfg = TradingConfig(config_file='nonexistent.json')
        assert cfg.is_test_mode() is True

    def test_is_test_mode_false_when_configured(self, temp_dir):
        cfg = TradingConfig(config_file=str(temp_dir / 'prod_mode.json'))
        cfg.set('test_mode', False)
        assert cfg.is_test_mode() is False

# coding=utf-8
"""
配置文件
用于存储API密钥和其他配置参数
"""

import os
import base64
import json
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class SecureConfig:
    """安全配置管理类"""

    def __init__(self, env: str = None):
        self._ensure_env_file()      # 自动检查并生成 .env 文件
        self._key_file = Path('.secret_key')
        self._encrypted_file = Path('.encrypted_config')
        self._config_file = Path('config.json')  # 主配置文件
        self._ensure_config_file()   # 自动检查并生成 config.json 文件

        # 优先级: 参数 > 环境变量 > config.json > 默认
        self.env = (
            env or
            self._get_from_env_or_file('ENV') or
            self._get_from_env_or_file('APP_ENV') or
            'development'
        )

        self.proxy_port = self._get_from_env_or_file('PROXY_PORT', default=6823, cast=int)
        self._api_key = self._get_from_env_or_file('BINANCE_API_KEY')
        self._secret = self._get_from_env_or_file('BINANCE_SECRET')

        self.config = self._load_config()

    def _ensure_env_file(self):
        env_path = Path('.env')
        if not env_path.exists():
            env_content = (
                "# QuantTrade 环境配置\n"
                "ENV=development\n"
                "PROXY_PORT=6823\n"
                "BINANCE_API_KEY=your_api_key_here\n"
                "BINANCE_SECRET=your_secret_here\n"
            )
            env_path.write_text(env_content, encoding='utf-8')
            print("✅ 已自动生成 .env 文件，请根据实际情况填写 API KEY 和 SECRET。")

    def _ensure_config_file(self):
        config_path = self._config_file
        if not config_path.exists():
            default_config = {
                "timeout": 10000,
                "enableRateLimit": True,
                "proxies": {
                    "http": "http://127.0.0.1:6823",
                    "https": "http://127.0.0.1:6823"
                },
                "sandbox": False
            }
            config_path.write_text(json.dumps(default_config, indent=2), encoding='utf-8')
            print("✅ 已自动生成 config.json 文件，请根据实际情况修改。")

    def _get_from_env_or_file(self, key, default=None, cast=None):
        # 1. 环境变量
        value = os.getenv(key)
        if value is not None:
            return cast(value) if cast else value
        # 2. config.json 文件
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if key in data:
                    return cast(data[key]) if cast else data[key]
            except Exception as e:
                print(f"读取配置文件 {self._config_file} 失败: {e}")
        # 3. 默认值
        return default

    def _generate_key(self) -> bytes:
        return Fernet.generate_key()

    def _get_or_create_key(self) -> bytes:
        if self._key_file.exists():
            return self._key_file.read_bytes()
        else:
            key = self._generate_key()
            self._key_file.write_bytes(key)
            return key

    def _encrypt_data(self, data: str) -> str:
        key = self._get_or_create_key()
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        key = self._get_or_create_key()
        f = Fernet(key)
        return f.decrypt(encrypted_data.encode()).decode()

    def _save_encrypted_config(self, config_data: Dict[str, str]):
        encrypted_data = self._encrypt_data(json.dumps(config_data))
        self._encrypted_file.write_text(encrypted_data)

    def _load_encrypted_config(self) -> Optional[Dict[str, str]]:
        if not self._encrypted_file.exists():
            return None
        try:
            encrypted_data = self._encrypted_file.read_text()
            decrypted_data = self._decrypt_data(encrypted_data)
            return json.loads(decrypted_data)
        except Exception as e:
            print(f"加载加密配置失败: {e}")
            return None

    def _load_config(self) -> Dict[str, Any]:
        self._ensure_config_file()
        # 读取 config.json
        with open(self._config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # 用 .env 或环境变量覆盖
        def override(key, cast=None):
            v = self._get_from_env_or_file(key, default=None, cast=cast)
            if v is not None:
                config[key] = v
        override('timeout', cast=int)
        override('enableRateLimit', cast=lambda x: str(x).lower() in ('1', 'true', 'yes'))
        proxies = self._get_from_env_or_file('PROXIES', default=None)
        if proxies:
            try:
                config['proxies'] = json.loads(proxies)
            except Exception:
                print("PROXIES 配置格式错误，需为json字符串")
        sandbox = self._get_from_env_or_file('SANDBOX', default=None)
        if sandbox is not None:
            config['sandbox'] = str(sandbox).lower() in ('1', 'true', 'yes')
        # 删除 urls 相关逻辑
        return config

    def _get_api_credentials(self) -> Optional[Dict[str, str]]:
        # 1. 构造参数或.env/config.json
        if self._api_key and self._secret:
            print("✅ 使用配置文件或环境变量中的API密钥")
            return {'apiKey': self._api_key, 'secret': self._secret}
        # 2. 加密配置文件
        encrypted_config = self._load_encrypted_config()
        if encrypted_config and 'apiKey' in encrypted_config and 'secret' in encrypted_config:
            print("✅ 使用加密配置文件中的API密钥")
            return encrypted_config
        # 3. 默认值（仅开发环境）
        if self.env == 'development':
            print("⚠️  使用默认API密钥（仅用于开发测试）")
            return {
                'apiKey': 'yBRGbWLRGxPfxTE4BxQO8LPzZ7GISRgrlhkJdNg95FIqjDf7Is0p3EHP6hZkUFQC',
                'secret': 'fnocUgpR443EliLmjV3lTIgU0Sb3UNERprE2GZQJR8kK6gWzDKxWbyAWTt592TPl',
            }
        return None

    def get_binance_config(self) -> Dict[str, Any]:
        config = self.config.copy()
        credentials = self._get_api_credentials()
        if credentials:
            config.update(credentials)
        else:
            raise ValueError(
                f"未找到API密钥！请在 .env 或 config.json 设置 BINANCE_API_KEY 和 BINANCE_SECRET，"
                f"或使用 save_credentials() 方法保存加密配置。"
            )
        return config

    def get_public_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def save_credentials(self, api_key: str, secret: str):
        config_data = {
            'apiKey': api_key,
            'secret': secret,
            'env': self.env
        }
        self._save_encrypted_config(config_data)
        print("✅ API密钥已加密保存到 .encrypted_config 文件")

    def clear_credentials(self):
        if self._encrypted_file.exists():
            self._encrypted_file.unlink()
            print("✅ 已清除保存的API密钥")
        if self._key_file.exists():
            self._key_file.unlink()
            print("✅ 已清除加密密钥")

    def validate_credentials(self) -> bool:
        try:
            import ccxt
            config = self.get_binance_config()
            exchange = ccxt.binance(config)
            exchange.fetch_balance()
            print("✅ API密钥验证成功")
            return True
        except Exception as e:
            print(f"❌ API密钥验证失败: {e}")
            return False

# 创建默认配置实例
config = SecureConfig()

# 为了向后兼容，保留原来的Config类名
Config = SecureConfig 
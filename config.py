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

class SecureConfig:
    """安全配置管理类"""
    
    def __init__(self, env: str = 'development'):
        """
        初始化配置
        :param env: 环境类型 ('development', 'test', 'production')
        """
        self.env = env
        self.config = self._load_config()
        self._key_file = Path('.secret_key')
        self._encrypted_file = Path('.encrypted_config')
        
    def _generate_key(self) -> bytes:
        """生成加密密钥"""
        return Fernet.generate_key()
    
    def _get_or_create_key(self) -> bytes:
        """获取或创建加密密钥"""
        if self._key_file.exists():
            return self._key_file.read_bytes()
        else:
            key = self._generate_key()
            self._key_file.write_bytes(key)
            return key
    
    def _encrypt_data(self, data: str) -> str:
        """加密数据"""
        key = self._get_or_create_key()
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """解密数据"""
        key = self._get_or_create_key()
        f = Fernet(key)
        return f.decrypt(encrypted_data.encode()).decode()
    
    def _save_encrypted_config(self, config_data: Dict[str, str]):
        """保存加密配置"""
        encrypted_data = self._encrypt_data(json.dumps(config_data))
        self._encrypted_file.write_text(encrypted_data)
    
    def _load_encrypted_config(self) -> Optional[Dict[str, str]]:
        """加载加密配置"""
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
        """加载配置"""
        # 基础配置
        base_config = {
            'timeout': 10000,
            'enableRateLimit': True,
            # 'options':{
            #   'adjustForTimeDifference': False
            # },
            'proxies': {
                'http': 'http://127.0.0.1:10311',
                'https': 'http://127.0.0.1:10311',
            }
        }
        
        # 环境特定配置
        if self.env == 'test':
            # 测试网配置
            base_config.update({
                'sandbox': True,
                'urls': {
                    'api': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                    },
                    'test': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                    }
                }
            })
        
        return base_config
    
    def _get_api_credentials(self) -> Optional[Dict[str, str]]:
        """
        按优先级获取API凭证
        优先级：环境变量 > 加密文件 > 默认值（仅开发环境）
        """
        # 1. 环境变量（最高优先级）
        api_key = os.getenv('BINANCE_API_KEY')
        secret = os.getenv('BINANCE_SECRET')
        
        if api_key and secret:
            print("✅ 使用环境变量中的API密钥")
            return {'apiKey': api_key, 'secret': secret}
        
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
        """获取币安配置"""
        config = self.config.copy()
        
        credentials = self._get_api_credentials()
        if credentials:
            config.update(credentials)
        else:
            raise ValueError(
                f"未找到API密钥！请设置环境变量 BINANCE_API_KEY 和 BINANCE_SECRET，"
                f"或使用 save_credentials() 方法保存加密配置。"
            )
        
        return config
    
    def get_public_config(self) -> Dict[str, Any]:
        """获取公共配置（不需要API密钥）"""
        return self.config.copy()
    
    def save_credentials(self, api_key: str, secret: str):
        """
        保存API密钥到加密文件
        :param api_key: API密钥
        :param secret: API密钥
        """
        config_data = {
            'apiKey': api_key,
            'secret': secret,
            'env': self.env
        }
        self._save_encrypted_config(config_data)
        print("✅ API密钥已加密保存到 .encrypted_config 文件")
    
    def clear_credentials(self):
        """清除保存的API密钥"""
        if self._encrypted_file.exists():
            self._encrypted_file.unlink()
            print("✅ 已清除保存的API密钥")
        if self._key_file.exists():
            self._key_file.unlink()
            print("✅ 已清除加密密钥")
    
    def validate_credentials(self) -> bool:
        """验证API密钥是否有效"""
        try:
            import ccxt
            config = self.get_binance_config()
            exchange = ccxt.binance(config)
            # 尝试获取账户信息来验证密钥
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
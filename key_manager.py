# coding=utf-8
"""
API密钥管理工具
提供安全的密钥存储、验证和管理功能
"""

import getpass
import argparse
from config import SecureConfig

def save_credentials_interactive():
    """交互式保存API密钥"""
    print("🔐 安全保存API密钥")
    print("=" * 50)
    
    # 获取API密钥
    api_key = getpass.getpass("请输入币安API Key: ")
    secret = getpass.getpass("请输入币安Secret: ")
    
    if not api_key or not secret:
        print("❌ API密钥不能为空")
        return False
    
    # 选择环境
    print("\n选择环境:")
    print("1. development (开发环境)")
    print("2. test (测试网)")
    print("3. production (生产环境)")
    
    env_choice = input("请选择环境 (1-3): ").strip()
    env_map = {
        '1': 'development',
        '2': 'test', 
        '3': 'production'
    }
    
    env = env_map.get(env_choice, 'development')
    
    try:
        # 保存密钥
        config = SecureConfig(env=env)
        config.save_credentials(api_key, secret)
        
        # 验证密钥
        print("\n🔍 验证API密钥...")
        if config.validate_credentials():
            print(f"✅ API密钥已成功保存并验证，环境: {env}")
            return True
        else:
            print("❌ API密钥验证失败，请检查密钥是否正确")
            config.clear_credentials()
            return False
            
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

def validate_credentials():
    """验证已保存的API密钥"""
    print("🔍 验证API密钥")
    print("=" * 30)
    
    try:
        config = SecureConfig()
        if config.validate_credentials():
            print("✅ API密钥有效")
            return True
        else:
            print("❌ API密钥无效")
            return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def clear_credentials():
    """清除已保存的API密钥"""
    print("🗑️  清除API密钥")
    print("=" * 30)
    
    confirm = input("确定要清除所有保存的API密钥吗？(y/N): ").strip().lower()
    if confirm == 'y':
        try:
            config = SecureConfig()
            config.clear_credentials()
            print("✅ API密钥已清除")
            return True
        except Exception as e:
            print(f"❌ 清除失败: {e}")
            return False
    else:
        print("❌ 操作已取消")
        return False

def show_status():
    """显示密钥状态"""
    print("📊 API密钥状态")
    print("=" * 30)
    
    config = SecureConfig()
    
    # 检查环境变量
    import os
    env_api_key = os.getenv('BINANCE_API_KEY')
    env_secret = os.getenv('BINANCE_SECRET')
    
    print(f"环境变量: {'✅ 已设置' if env_api_key and env_secret else '❌ 未设置'}")
    
    # 检查加密文件
    from pathlib import Path
    encrypted_file = Path('.encrypted_config')
    key_file = Path('.secret_key')
    
    print(f"加密文件: {'✅ 已保存' if encrypted_file.exists() else '❌ 未保存'}")
    print(f"加密密钥: {'✅ 已生成' if key_file.exists() else '❌ 未生成'}")
    
    # 验证密钥
    try:
        if config.validate_credentials():
            print("密钥验证: ✅ 有效")
        else:
            print("密钥验证: ❌ 无效")
    except Exception as e:
        print(f"密钥验证: ❌ 错误 - {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='API密钥管理工具')
    parser.add_argument('action', choices=['save', 'validate', 'clear', 'status'], 
                       help='操作类型')
    
    args = parser.parse_args()
    
    if args.action == 'save':
        save_credentials_interactive()
    elif args.action == 'validate':
        validate_credentials()
    elif args.action == 'clear':
        clear_credentials()
    elif args.action == 'status':
        show_status()

if __name__ == '__main__':
    main() 
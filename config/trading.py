#!/usr/bin/env python3
"""
交易配置模块
用于管理实盘和测试模式的配置
"""

import os
from typing import Dict, Any

class TradingConfig:
    """交易配置管理器"""
    
    def __init__(self, config_file: str = 'trading_config.json'):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        import json
        
        default_config = {
            # 基础配置
            'test_mode': True,  # 默认测试模式
            'symbol': 'BTC/USDT',
            'strategy': 'mean_reversion',
            'initial_capital': 10000,
            'check_interval': 60,  # 秒
            
            # 风险管理
            'max_position_size': 0.1,  # 最大仓位比例
            'max_daily_loss': 0.05,    # 最大日亏损
            
            # 交易参数
            'commission_rate': 0.001,  # 手续费率
            'min_trade_amount': 10,    # 最小交易金额
            
            # API配置
            'api_key': '',
            'api_secret': '',
            'exchange': 'binance',
            'testnet': True,  # 是否使用测试网
            
            # 数据库配置
            'db_path': 'quanttrade.db',
            'save_to_excel': True,
            
            # 通知配置
            'enable_notifications': False,
            'notification_method': 'console',  # console, email, webhook
            
            # 日志配置
            'log_level': 'INFO',
            'log_file': 'trading.log'
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并用户配置和默认配置
                    default_config.update(user_config)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
        
        return default_config
    
    def save_config(self):
        """保存配置文件"""
        import json
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"配置已保存到 {self.config_file}")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
    
    def is_test_mode(self) -> bool:
        """是否为测试模式"""
        return self.config.get('test_mode', True)
    
    def get_api_credentials(self) -> tuple:
        """获取API凭证"""
        api_key = self.config.get('api_key') or os.getenv('BINANCE_API_KEY')
        api_secret = self.config.get('api_secret') or os.getenv('BINANCE_SECRET')
        return api_key, api_secret
    
    def validate_config(self) -> bool:
        """验证配置"""
        errors = []
        
        # 检查必要配置
        if not self.is_test_mode():
            api_key, api_secret = self.get_api_credentials()
            if not api_key or not api_secret:
                errors.append("实盘模式需要配置API密钥")
        
        # 检查数值配置
        if self.config.get('max_position_size', 0) <= 0 or self.config.get('max_position_size', 0) > 1:
            errors.append("最大仓位比例必须在0-1之间")
        
        if self.config.get('max_daily_loss', 0) <= 0 or self.config.get('max_daily_loss', 0) > 1:
            errors.append("最大日亏损必须在0-1之间")
        
        if self.config.get('commission_rate', 0) < 0:
            errors.append("手续费率不能为负数")
        
        if errors:
            print("❌ 配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def print_config(self):
        """打印当前配置"""
        print("📋 当前配置:")
        print("="*50)
        
        # 基础配置
        print(f"模式: {'测试模式' if self.is_test_mode() else '实盘模式'}")
        print(f"交易对: {self.config.get('symbol')}")
        print(f"策略: {self.config.get('strategy')}")
        print(f"初始资金: ${self.config.get('initial_capital')}")
        print(f"检查间隔: {self.config.get('check_interval')}秒")
        
        # 风险管理
        print(f"最大仓位: {self.config.get('max_position_size')*100:.1f}%")
        print(f"最大日亏损: {self.config.get('max_daily_loss')*100:.1f}%")
        print(f"手续费率: {self.config.get('commission_rate')*100:.3f}%")
        
        # API配置
        if not self.is_test_mode():
            api_key, api_secret = self.get_api_credentials()
            print(f"API密钥: {'已配置' if api_key else '未配置'}")
            print(f"交易所: {self.config.get('exchange')}")
            print(f"测试网: {'是' if self.config.get('testnet') else '否'}")
        
        print("="*50)
    
    def interactive_config(self):
        """交互式配置"""
        print("🔧 交互式配置")
        print("="*50)
        
        # 模式选择
        print("1. 选择模式:")
        print("   1) 测试模式 (推荐)")
        print("   2) 实盘模式")
        mode_choice = input("请选择 (1-2): ").strip()
        self.config['test_mode'] = (mode_choice == '1')
        
        # 交易对选择
        print("\n2. 选择交易对:")
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT']
        for i, symbol in enumerate(symbols, 1):
            print(f"   {i}) {symbol}")
        symbol_choice = input("请选择 (1-4): ").strip()
        if symbol_choice.isdigit() and 1 <= int(symbol_choice) <= len(symbols):
            self.config['symbol'] = symbols[int(symbol_choice) - 1]
        
        # 策略选择
        print("\n3. 选择策略:")
        strategies = ['mean_reversion', 'ma_cross', 'rsi_signal', 'bollinger_breakout']
        for i, strategy in enumerate(strategies, 1):
            print(f"   {i}) {strategy}")
        strategy_choice = input("请选择 (1-4): ").strip()
        if strategy_choice.isdigit() and 1 <= int(strategy_choice) <= len(strategies):
            self.config['strategy'] = strategies[int(strategy_choice) - 1]
        
        # 初始资金
        print("\n4. 设置初始资金:")
        capital_input = input("请输入初始资金 (默认10000): ").strip()
        if capital_input:
            try:
                self.config['initial_capital'] = float(capital_input)
            except ValueError:
                print("输入无效，使用默认值")
        
        # 风险管理
        print("\n5. 风险管理设置:")
        position_size = input("最大仓位比例 (0.1 = 10%, 默认0.1): ").strip()
        if position_size:
            try:
                self.config['max_position_size'] = float(position_size)
            except ValueError:
                print("输入无效，使用默认值")
        
        daily_loss = input("最大日亏损比例 (0.05 = 5%, 默认0.05): ").strip()
        if daily_loss:
            try:
                self.config['max_daily_loss'] = float(daily_loss)
            except ValueError:
                print("输入无效，使用默认值")
        
        # 实盘模式特殊配置
        if not self.is_test_mode():
            print("\n6. API配置:")
            api_key = input("请输入API Key (或留空使用环境变量): ").strip()
            if api_key:
                self.config['api_key'] = api_key
            
            api_secret = input("请输入API Secret (或留空使用环境变量): ").strip()
            if api_secret:
                self.config['api_secret'] = api_secret
        
        # 保存配置
        self.save_config()
        print("\n✅ 配置完成！")

def main():
    """主函数"""
    config = TradingConfig()
    
    print("🔧 交易配置管理")
    print("="*50)
    print("1. 查看当前配置")
    print("2. 交互式配置")
    print("3. 验证配置")
    print("4. 重置为默认配置")
    print("0. 退出")
    
    choice = input("\n请选择 (0-4): ").strip()
    
    if choice == '1':
        config.print_config()
    elif choice == '2':
        config.interactive_config()
    elif choice == '3':
        if config.validate_config():
            print("✅ 配置验证通过")
        else:
            print("❌ 配置验证失败")
    elif choice == '4':
        import json
        config.config = {}
        config.save_config()
        print("✅ 配置已重置")
    elif choice == '0':
        print("👋 再见！")
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()

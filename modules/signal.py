import pandas as pd
from typing import Dict, List, Any
from datetime import datetime

class SignalSender:
    def __init__(self):
        """初始化信号发送器"""
        self.signal_history = []
    
    def send_terminal(self, signals: pd.Series):
        """
        输出信号到终端
        :param signals: 交易信号序列
        """
        print("\n📢 交易信号输出")
        print("=" * 50)
        
        # 统计信号
        buy_signals = signals[signals == 1]
        sell_signals = signals[signals == -1]
        
        print(f"买入信号数量: {len(buy_signals)}")
        print(f"卖出信号数量: {len(sell_signals)}")
        
        # 显示最近的信号
        recent_signals = signals.tail(10)
        print("\n最近10个信号:")
        for timestamp, signal in recent_signals.items():
            if signal != 0:
                signal_type = "买入" if signal == 1 else "卖出"
                print(f"  {timestamp}: {signal_type}")
        
        # 保存信号历史
        for timestamp, signal in signals[signals != 0].items():
            self.signal_history.append({
                'timestamp': timestamp,
                'signal': signal,
                'type': '买入' if signal == 1 else '卖出'
            })
    
    def send_other(self, signals: pd.Series, method: str = 'log'):
        """
        扩展：如邮件、微信、钉钉等
        :param signals: 交易信号序列
        :param method: 推送方式
        """
        if method == 'log':
            self._log_signals(signals)
        elif method == 'email':
            self._send_email(signals)
        elif method == 'webhook':
            self._send_webhook(signals)
        else:
            print(f"⚠️  不支持的推送方式: {method}")
    
    def _log_signals(self, signals: pd.Series):
        """记录信号到日志文件"""
        import os
        from datetime import datetime
        
        # 创建logs目录
        os.makedirs('logs', exist_ok=True)
        
        # 写入日志
        log_file = f"logs/signals_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            for timestamp, signal in signals[signals != 0].items():
                signal_type = "买入" if signal == 1 else "卖出"
                log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {timestamp}: {signal_type}\n"
                f.write(log_entry)
        
        print(f"✅ 信号已记录到: {log_file}")
    
    def _send_email(self, signals: pd.Series):
        """发送邮件通知（需要配置SMTP）"""
        print("📧 邮件推送功能需要配置SMTP服务器")
        # 这里可以集成邮件发送功能
        # 例如使用 smtplib 发送邮件
    
    def _send_webhook(self, signals: pd.Series):
        """发送Webhook通知（如钉钉、企业微信）"""
        print("🔗 Webhook推送功能需要配置Webhook URL")
        # 这里可以集成Webhook推送功能
        # 例如使用 requests 发送HTTP请求
    
    def get_signal_summary(self) -> Dict[str, Any]:
        """获取信号摘要"""
        if not self.signal_history:
            return {}
        
        df = pd.DataFrame(self.signal_history)
        
        summary = {
            'total_signals': len(df),
            'buy_signals': len(df[df['signal'] == 1]),
            'sell_signals': len(df[df['signal'] == -1]),
            'latest_signal': df.iloc[-1].to_dict() if len(df) > 0 else None,
            'signal_timeline': df.tail(10).to_dict('records')
        }
        
        return summary
    
    def print_signal_summary(self):
        """打印信号摘要"""
        summary = self.get_signal_summary()
        if not summary:
            print("❌ 没有信号历史")
            return
        
        print("\n📊 信号摘要")
        print("=" * 30)
        print(f"总信号数: {summary['total_signals']}")
        print(f"买入信号: {summary['buy_signals']}")
        print(f"卖出信号: {summary['sell_signals']}")
        
        if summary['latest_signal']:
            latest = summary['latest_signal']
            print(f"最新信号: {latest['timestamp']} - {latest['type']}")
        
        print("\n最近信号:")
        for signal in summary['signal_timeline'][-5:]:
            print(f"  {signal['timestamp']}: {signal['type']}")
    
    def clear_history(self):
        """清除信号历史"""
        self.signal_history.clear()
        print("✅ 信号历史已清除") 
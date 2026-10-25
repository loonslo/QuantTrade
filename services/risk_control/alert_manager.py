# -*- coding: utf-8 -*-
"""
风控预警管理器
支持多种预警通道：日志、推送、邮件
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import os

from utils.core.logger_manager import get_logger


class AlertChannel(Enum):
    """预警通道"""
    LOG = "log"
    WEBHOOK = "webhook"
    FILE = "file"
    CONSOLE = "console"


class AlertManager:
    """预警管理器"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化预警管理器
        
        Args:
            config: 配置 {
                "channels": ["log", "webhook"],
                "webhook_url": "https://...",
                "alert_file": "data/alerts.json",
                "min_level": "WARNING"
            }
        """
        self.logger = get_logger("alert_manager")
        self.config = config or {}
        self.channels = self.config.get("channels", ["log"])
        self.webhook_url = self.config.get("webhook_url")
        self.alert_file = self.config.get("alert_file", "logs/alerts.json")
        self.min_level = self.config.get("min_level", "WARNING")
        self._alert_history: List[Dict] = []
        self._callbacks: List[Callable] = []

    def register_callback(self, callback: Callable[[Dict], None]):
        """注册预警回调函数"""
        self._callbacks.append(callback)

    def send(self, level: str, code: str, message: str, symbol: str = None, **kwargs):
        """
        发送预警
        
        Args:
            level: INFO / WARNING / ERROR / CRITICAL
            code: 预警代码
            message: 预警消息
            symbol: 涉及标的
            **kwargs: 其他数据
        """
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "code": code,
            "message": message,
            "symbol": symbol,
            **kwargs
        }
        
        # 记录历史
        self._alert_history.append(alert)
        
        # 调用回调
        for cb in self._callbacks:
            try:
                cb(alert)
            except Exception as e:
                self.logger.error(f"预警回调执行失败: {e}")
        
        # 发送至各通道
        for channel in self.channels:
            try:
                self._send_to_channel(channel, alert)
            except Exception as e:
                self.logger.error(f"预警通道 {channel} 发送失败: {e}")
        
        # CRITICAL 级别同时写日志
        if level == "CRITICAL":
            self.logger.critical(f"[{code}] {message} | symbol={symbol}")

    def _send_to_channel(self, channel: str, alert: Dict):
        """发送至指定通道"""
        if channel == "log":
            self._send_to_log(alert)
        elif channel == "webhook":
            self._send_to_webhook(alert)
        elif channel == "file":
            self._send_to_file(alert)
        elif channel == "console":
            self._send_to_console(alert)

    def _send_to_log(self, alert: Dict):
        """写日志"""
        level_map = {
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "CRITICAL": self.logger.critical
        }
        fn = level_map.get(alert["level"], self.logger.info)
        fn(f"[{alert['code']}] {alert['message']}")

    def _send_to_console(self, alert: Dict):
        """打印到控制台"""
        symbol = alert.get("symbol", "-")
        print(f"🚨 [{alert['level']}] {alert['code']} | {symbol} | {alert['message']}")

    def _send_to_webhook(self, alert: Dict):
        """POST 到 Webhook"""
        if not self.webhook_url:
            return
        
        import requests
        try:
            # 飞书/钉钉/企业微信 webhook 格式
            payload = {
                "msgtype": "text",
                "text": {
                    "content": f"🚨 [{alert['level']}] {alert['code']}\n{alert['message']}\n标的: {alert.get('symbol', 'N/A')}\n时间: {alert['timestamp']}"
                }
            }
            requests.post(self.webhook_url, json=payload, timeout=5)
        except Exception as e:
            self.logger.error(f"Webhook 发送失败: {e}")

    def _send_to_file(self, alert: Dict):
        """追加写入文件"""
        os.makedirs(os.path.dirname(self.alert_file), exist_ok=True)
        with open(self.alert_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert, ensure_ascii=False) + "\n")

    def get_alert_history(
        self,
        level: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """查询预警历史"""
        results = self._alert_history
        
        if level:
            results = [a for a in results if a["level"] == level]
        if symbol:
            results = [a for a in results if a.get("symbol") == symbol]
        
        return results[-limit:]

    def clear_history(self):
        """清空预警历史"""
        self._alert_history.clear()

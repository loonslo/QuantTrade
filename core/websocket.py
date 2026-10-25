"""
WebSocket实时推送模块

提供实时数据推送功能：
- K线数据推送
- 交易信号推送
- 持仓更新推送
- 系统通知推送

使用示例：
    from core.websocket import WebSocketManager, KLineSubscriber

    manager = WebSocketManager()
    manager.start()

    # 订阅K线数据
    subscriber = manager.subscribe_kline('BTCUSDT', '1m', callback)
    manager.unsubscribe(subscriber)

    manager.stop()
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime
import asyncio
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    KLINE = 'kline'
    TRADE = 'trade'
    SIGNAL = 'signal'
    POSITION = 'position'
    ORDER = 'order'
    NOTIFICATION = 'notification'
    HEARTBEAT = 'heartbeat'


@dataclass
class Subscriber:
    """订阅者"""
    id: str
    channel: str
    callback: Callable
    filters: Dict = None


class BaseChannel(ABC):
    """频道基类"""

    @abstractmethod
    def publish(self, data: Dict[str, Any]):
        """发布消息"""
        pass

    @abstractmethod
    def subscribe(self, callback: Callable, filters: Dict = None) -> str:
        """订阅消息"""
        pass

    @abstractmethod
    def unsubscribe(self, subscriber_id: str):
        """取消订阅"""
        pass


class KLineChannel(BaseChannel):
    """K线数据频道"""

    def __init__(self, symbol: str, timeframe: str):
        self.symbol = symbol
        self.timeframe = timeframe
        self.subscribers: Dict[str, Subscriber] = {}

    def publish(self, data: Dict[str, Any]):
        """发布K线数据"""
        for subscriber in self.subscribers.values():
            try:
                subscriber.callback(data)
            except Exception as e:
                logger.error(f"推送K线数据失败: {e}")

    def subscribe(self, callback: Callable, filters: Dict = None) -> str:
        import uuid
        sub_id = str(uuid.uuid4())[:8]
        self.subscribers[sub_id] = Subscriber(sub_id, f"kline:{self.symbol}:{self.timeframe}", callback, filters)
        logger.info(f"新增K线订阅: {self.symbol} {self.timeframe}")
        return sub_id

    def unsubscribe(self, subscriber_id: str):
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            logger.info(f"取消K线订阅: {subscriber_id}")


class SignalChannel(BaseChannel):
    """交易信号频道"""

    def __init__(self):
        self.subscribers: Dict[str, Subscriber] = {}
        self._signal_history: List[Dict] = []

    def publish(self, data: Dict[str, Any]):
        """发布交易信号"""
        self._signal_history.append({
            **data,
            'timestamp': datetime.now().isoformat()
        })
        # 只保留最近100条
        if len(self._signal_history) > 100:
            self._signal_history = self._signal_history[-100:]

        for subscriber in self.subscribers.values():
            try:
                subscriber.callback(data)
            except Exception as e:
                logger.error(f"推送信号失败: {e}")

    def subscribe(self, callback: Callable, filters: Dict = None) -> str:
        import uuid
        sub_id = str(uuid.uuid4())[:8]
        self.subscribers[sub_id] = Subscriber(sub_id, "signal", callback, filters)
        # 发送历史信号
        if filters and filters.get('include_history', False):
            for signal in self._signal_history[-10:]:
                try:
                    callback(signal)
                except:
                    pass
        return sub_id

    def unsubscribe(self, subscriber_id: str):
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]


class WebSocketManager:
    """
    WebSocket管理器

    管理所有频道和订阅者。
    """

    def __init__(self):
        self.channels: Dict[str, BaseChannel] = {}
        self._running = False
        self._heartbeat_task = None
        self._init_default_channels()

    def _init_default_channels(self):
        """初始化默认频道"""
        self.channels['signal'] = SignalChannel()

    def _get_kline_channel(self, symbol: str, timeframe: str) -> KLineChannel:
        """获取或创建K线频道"""
        key = f"kline:{symbol}:{timeframe}"
        if key not in self.channels:
            self.channels[key] = KLineChannel(symbol, timeframe)
        return self.channels[key]

    def start(self):
        """启动管理器"""
        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("WebSocket管理器已启动")

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                self.broadcast(MessageType.HEARTBEAT.value, {'timestamp': datetime.now().isoformat()})
                await asyncio.sleep(30)  # 每30秒发送心跳
            except Exception as e:
                logger.error(f"心跳错误: {e}")
                break

    def stop(self):
        """停止管理器"""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        logger.info("WebSocket管理器已停止")

    def subscribe_kline(self, symbol: str, timeframe: str,
                        callback: Callable, filters: Dict = None) -> str:
        """订阅K线数据"""
        channel = self._get_kline_channel(symbol, timeframe)
        return channel.subscribe(callback, filters)

    def unsubscribe_kline(self, subscriber_id: str, symbol: str, timeframe: str):
        """取消K线订阅"""
        key = f"kline:{symbol}:{timeframe}"
        if key in self.channels:
            self.channels[key].unsubscribe(subscriber_id)

    def subscribe_signal(self, callback: Callable, filters: Dict = None) -> str:
        """订阅交易信号"""
        channel = self.channels['signal']
        return channel.subscribe(callback, filters)

    def publish_signal(self, signal_type: str, symbol: str,
                       action: str, price: float, **kwargs):
        """发布交易信号"""
        signal_data = {
            'type': signal_type,
            'symbol': symbol,
            'action': action,
            'price': price,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        channel = self.channels.get('signal')
        if channel:
            channel.publish(signal_data)
            logger.info(f"发布信号: {signal_type} {symbol} {action} @ {price}")

    def publish_kline(self, symbol: str, timeframe: str, kline_data: Dict):
        """发布K线数据"""
        channel = self._get_kline_channel(symbol, timeframe)
        channel.publish({
            'symbol': symbol,
            'timeframe': timeframe,
            'data': kline_data,
            'timestamp': datetime.now().isoformat()
        })

    def broadcast(self, message_type: str, data: Dict):
        """广播消息到所有订阅者"""
        for channel in self.channels.values():
            if hasattr(channel, 'subscribers'):
                for subscriber in channel.subscribers.values():
                    try:
                        subscriber.callback({
                            'type': message_type,
                            'data': data,
                            'timestamp': datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.error(f"广播消息失败: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        channel_stats = {}
        for key, channel in self.channels.items():
            if hasattr(channel, 'subscribers'):
                channel_stats[key] = len(channel.subscribers)

        return {
            'running': self._running,
            'channels': len(self.channels),
            'subscribers': sum(len(c.subscribers) for c in self.channels.values()
                              if hasattr(c, 'subscribers')),
            'channel_stats': channel_stats
        }


class SignalPublisher:
    """
    信号发布器

    便捷发布交易信号的工具类。
    """

    def __init__(self, manager: WebSocketManager = None):
        self.manager = manager or WebSocketManager()
        self.manager.start()

    def publish_buy_signal(self, symbol: str, strategy: str,
                           price: float, **kwargs):
        """发布买入信号"""
        self.manager.publish_signal(
            signal_type='buy_signal',
            symbol=symbol,
            action='buy',
            price=price,
            strategy=strategy,
            **kwargs
        )

    def publish_sell_signal(self, symbol: str, strategy: str,
                            price: float, **kwargs):
        """发布卖出信号"""
        self.manager.publish_signal(
            signal_type='sell_signal',
            symbol=symbol,
            action='sell',
            price=price,
            strategy=strategy,
            **kwargs
        )

    def publish_exit_signal(self, symbol: str, strategy: str,
                            price: float, reason: str = None, **kwargs):
        """发布平仓信号"""
        self.manager.publish_signal(
            signal_type='exit_signal',
            symbol=symbol,
            action='exit',
            price=price,
            strategy=strategy,
            reason=reason,
            **kwargs
        )

    def stop(self):
        """停止发布器"""
        self.manager.stop()


# 全局实例
_ws_manager: Optional[WebSocketManager] = None


def get_ws_manager() -> WebSocketManager:
    """获取全局WebSocket管理器"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager


def get_signal_publisher() -> SignalPublisher:
    """获取信号发布器"""
    return SignalPublisher(get_ws_manager())


if __name__ == '__main__':
    # 测试
    manager = WebSocketManager()
    manager.start()

    def on_signal(data):
        print(f"收到信号: {data}")

    def on_kline(data):
        print(f"收到K线: {data['symbol']} {data['data']}")

    # 订阅信号
    sub_id = manager.subscribe_signal(on_signal, {'include_history': True})
    print(f"信号订阅ID: {sub_id}")

    # 订阅K线
    sub_id2 = manager.subscribe_kline('BTCUSDT', '1m', on_kline)
    print(f"K线订阅ID: {sub_id2}")

    # 发布测试信号
    manager.publish_signal('buy_signal', 'BTCUSDT', 'buy', 50000)
    manager.publish_kline('BTCUSDT', '1m', {'open': 50000, 'high': 50100, 'low': 49900, 'close': 50050})

    # 打印状态
    print(f"状态: {manager.get_status()}")

    # 停止
    manager.stop()

"""
WebSocket API
提供实时市场数据推送服务
"""

import asyncio
import json
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
from utils.time.format_utils import format_timestamp
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # 连接ID -> 订阅的币种列表
        self.symbol_connections: Dict[str, Set[str]] = {}  # 币种 -> 连接ID列表
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """建立WebSocket连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()
        logger.info(f"客户端 {client_id} 已连接")
    
    def disconnect(self, client_id: str):
        """断开WebSocket连接"""
        if client_id in self.active_connections:
            # 清理订阅关系
            subscribed_symbols = self.subscriptions.get(client_id, set())
            for symbol in subscribed_symbols:
                if symbol in self.symbol_connections:
                    self.symbol_connections[symbol].discard(client_id)
            
            # 清理连接记录
            del self.active_connections[client_id]
            del self.subscriptions[client_id]
            logger.info(f"客户端 {client_id} 已断开连接")
    
    async def subscribe(self, client_id: str, symbols: List[str], channels: List[str]):
        """订阅指定币种和频道的数据"""
        if client_id not in self.active_connections:
            raise ValueError("客户端未连接")
        
        # 更新订阅关系
        self.subscriptions[client_id] = set(symbols)
        
        # 更新币种到连接的映射
        for symbol in symbols:
            if symbol not in self.symbol_connections:
                self.symbol_connections[symbol] = set()
            self.symbol_connections[symbol].add(client_id)
        
        logger.info(f"客户端 {client_id} 订阅了 {symbols} 的 {channels} 频道")
        
        # 发送订阅确认
        await self.send_personal_message({
            "type": "subscription_confirmed",
            "symbols": symbols,
            "channels": channels,
            "timestamp": format_timestamp(datetime.now())
        }, client_id)
    
    async def unsubscribe(self, client_id: str, symbols: List[str]):
        """取消订阅指定币种的数据"""
        if client_id not in self.active_connections:
            return
        
        # 更新订阅关系
        current_subscriptions = self.subscriptions.get(client_id, set())
        for symbol in symbols:
            current_subscriptions.discard(symbol)
            if symbol in self.symbol_connections:
                self.symbol_connections[symbol].discard(client_id)
        
        logger.info(f"客户端 {client_id} 取消订阅了 {symbols}")
        
        # 发送取消订阅确认
        await self.send_personal_message({
            "type": "unsubscription_confirmed",
            "symbols": symbols,
            "timestamp": format_timestamp(datetime.now())
        }, client_id)
    
    async def broadcast_price_update(self, symbol: str, price_data: Dict):
        """广播价格更新到所有订阅该币种的客户端"""
        if symbol not in self.symbol_connections:
            return
        
        message = {
            "type": "price_update",
            "symbol": symbol,
            "data": price_data,
            "timestamp": format_timestamp(datetime.now())
        }
        
        # 发送给所有订阅该币种的客户端
        disconnected_clients = set()
        for client_id in self.symbol_connections[symbol]:
            try:
                await self.send_personal_message(message, client_id)
            except Exception as e:
                logger.error(f"发送价格更新到客户端 {client_id} 失败: {e}")
                disconnected_clients.add(client_id)
        
        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def broadcast_volume_update(self, symbol: str, volume_data: Dict):
        """广播成交量更新"""
        if symbol not in self.symbol_connections:
            return
        
        message = {
            "type": "volume_update",
            "symbol": symbol,
            "data": volume_data,
            "timestamp": format_timestamp(datetime.now())
        }
        
        disconnected_clients = set()
        for client_id in self.symbol_connections[symbol]:
            try:
                await self.send_personal_message(message, client_id)
            except Exception as e:
                logger.error(f"发送成交量更新到客户端 {client_id} 失败: {e}")
                disconnected_clients.add(client_id)
        
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def broadcast_trade_update(self, symbol: str, trade_data: Dict):
        """广播交易更新"""
        if symbol not in self.symbol_connections:
            return
        
        message = {
            "type": "trade_update",
            "symbol": symbol,
            "data": trade_data,
            "timestamp": format_timestamp(datetime.now())
        }
        
        disconnected_clients = set()
        for client_id in self.symbol_connections[symbol]:
            try:
                await self.send_personal_message(message, client_id)
            except Exception as e:
                logger.error(f"发送交易更新到客户端 {client_id} 失败: {e}")
                disconnected_clients.add(client_id)
        
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def send_personal_message(self, message: Dict, client_id: str):
        """发送个人消息给指定客户端"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"发送消息到客户端 {client_id} 失败: {e}")
                raise
    
    async def broadcast_system_message(self, message: Dict):
        """广播系统消息给所有连接的客户端"""
        disconnected_clients = set()
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"发送系统消息到客户端 {client_id} 失败: {e}")
                disconnected_clients.add(client_id)
        
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.active_connections)
    
    def get_subscription_stats(self) -> Dict:
        """获取订阅统计信息"""
        stats = {
            "total_connections": len(self.active_connections),
            "total_symbols": len(self.symbol_connections),
            "symbol_subscribers": {}
        }
        
        for symbol, connections in self.symbol_connections.items():
            stats["symbol_subscribers"][symbol] = len(connections)
        
        return stats


# 全局连接管理器实例
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket端点处理函数"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理不同类型的消息
            message_type = message.get("action")
            
            if message_type == "subscribe":
                symbols = message.get("symbols", [])
                channels = message.get("channels", [])
                await manager.subscribe(client_id, symbols, channels)
                
            elif message_type == "unsubscribe":
                symbols = message.get("symbols", [])
                await manager.unsubscribe(client_id, symbols)
                
            elif message_type == "ping":
                # 心跳检测
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": format_timestamp(datetime.now())
                }, client_id)
                
            elif message_type == "get_stats":
                # 获取连接统计信息
                stats = manager.get_subscription_stats()
                await manager.send_personal_message({
                    "type": "stats",
                    "data": stats,
                    "timestamp": format_timestamp(datetime.now())
                }, client_id)
                
            else:
                # 未知消息类型
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"未知的消息类型: {message_type}",
                    "timestamp": format_timestamp(datetime.now())
                }, client_id)
                
    except WebSocketDisconnect:
        logger.info(f"客户端 {client_id} WebSocket连接断开")
    except Exception as e:
        logger.error(f"处理WebSocket消息时发生错误: {e}")
    finally:
        manager.disconnect(client_id)


# 模拟实时数据推送（用于测试）
async def simulate_real_time_data():
    """模拟实时数据推送（仅用于测试）"""
    import random
    import time
    
    while True:
        try:
            # 模拟BTC价格更新
            btc_price = 115000 + random.uniform(-1000, 1000)
            await manager.broadcast_price_update("BTCUSDT", {
                "price": round(btc_price, 2),
                "change_24h": round(random.uniform(-5, 5), 2),
                "volume_24h": random.randint(20000000000, 30000000000)
            })
            
            # 模拟ETH价格更新
            eth_price = 3600 + random.uniform(-100, 100)
            await manager.broadcast_price_update("ETHUSDT", {
                "price": round(eth_price, 2),
                "change_24h": round(random.uniform(-3, 3), 2),
                "volume_24h": random.randint(15000000000, 20000000000)
            })
            
            # 等待5秒
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"模拟实时数据推送失败: {e}")
            await asyncio.sleep(5)


# 启动模拟数据推送任务
def start_simulation():
    """启动模拟数据推送（仅用于测试）"""
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(simulate_real_time_data())
        logger.info("模拟实时数据推送已启动")
    except Exception as e:
        logger.error(f"启动模拟数据推送失败: {e}")


if __name__ == "__main__":
    # 测试WebSocket功能
    logging.basicConfig(level=logging.INFO)
    start_simulation()
    
    try:
        loop = asyncio.get_event_loop()
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("WebSocket服务已停止") 
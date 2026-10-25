# -*- coding: utf-8 -*-
"""
数据同步配置
提供数据同步相关的配置参数
"""

from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class DataSyncConfig:
    """数据同步配置"""

    # 基础配置
    max_workers: int = 4
    batch_size: int = 1000
    max_retries: int = 3
    retry_delay_seconds: int = 60

    # 调度器配置
    enable_scheduler: bool = True
    scheduler_check_interval: int = 1  # 秒

    # 任务配置
    market_data_interval: int = 300     # 5分钟
    coin_details_interval: int = 3600   # 1小时
    fear_greed_interval: int = 1800     # 30分钟
    kline_data_interval: int = 60       # 1分钟
    popular_coins_interval: int = 900   # 15分钟

    # 数据保留策略（天）
    market_data_retention: int = 365    # 1年
    coin_details_retention: int = 90    # 3个月
    fear_greed_retention: int = 180     # 6个月
    kline_1m_retention: int = 180       # 6个月
    kline_1d_retention: int = 1825      # 5年
    popular_coins_retention: int = 30   # 1个月

    # API配置
    binance_api_timeout: int = 30
    coingecko_api_timeout: int = 30
    fear_greed_api_timeout: int = 30

    # 错误处理
    continue_on_error: bool = True
    log_level: str = "INFO"

# 默认配置实例
DEFAULT_CONFIG = DataSyncConfig()

def get_data_sync_config() -> DataSyncConfig:
    """获取数据同步配置"""
    try:
        from utils.core.config_manager import config_manager

        config_dict = config_manager.config
        sync_config = config_dict.get('data_sync', {})

        # 创建配置实例
        config = DataSyncConfig()

        # 更新配置
        for key, value in sync_config.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    except Exception:
        # 如果无法加载配置，返回默认配置
        return DEFAULT_CONFIG

def get_task_schedules() -> Dict[str, Dict[str, Any]]:
    """获取任务调度配置"""
    config = get_data_sync_config()

    return {
        'market_data_sync': {
            'schedule_type': 'interval',
            'interval_seconds': config.market_data_interval,
            'enabled': True,
            'max_retries': config.max_retries,
            'retry_delay_seconds': config.retry_delay_seconds
        },
        'coin_details_sync': {
            'schedule_type': 'interval',
            'interval_seconds': config.coin_details_interval,
            'enabled': True,
            'max_retries': config.max_retries,
            'retry_delay_seconds': config.retry_delay_seconds
        },
        'fear_greed_sync': {
            'schedule_type': 'interval',
            'interval_seconds': config.fear_greed_interval,
            'enabled': True,
            'max_retries': config.max_retries,
            'retry_delay_seconds': config.retry_delay_seconds
        },
        'kline_data_sync': {
            'schedule_type': 'interval',
            'interval_seconds': config.kline_data_interval,
            'enabled': True,
            'max_retries': config.max_retries,
            'retry_delay_seconds': config.retry_delay_seconds
        },
        'popular_coins_sync': {
            'schedule_type': 'interval',
            'interval_seconds': config.popular_coins_interval,
            'enabled': True,
            'max_retries': config.max_retries,
            'retry_delay_seconds': config.retry_delay_seconds
        }
    }

def get_retention_policies() -> Dict[str, int]:
    """获取数据保留策略"""
    config = get_data_sync_config()

    return {
        'market_data': config.market_data_retention,
        'coin_details': config.coin_details_retention,
        'fear_greed': config.fear_greed_retention,
        'kline_1m': config.kline_1m_retention,
        'kline_1d': config.kline_1d_retention,
        'popular_coins': config.popular_coins_retention
    }
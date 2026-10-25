# -*- coding: utf-8 -*-
"""
风控 API 路由
提供持仓监控、风险指标、预警管理等接口
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any
from datetime import datetime

from services.risk_control.position_monitor import PositionMonitor, AlertLevel, RiskAlert
from services.risk_control.risk_metrics import RiskCalculator
from services.risk_control.alert_manager import AlertManager
from utils.core.logger_manager import get_logger

router = APIRouter(prefix="/risk", tags=["风控"])
logger = get_logger("risk_control_api")

# 全局实例
_position_monitor = PositionMonitor()
_risk_calculator = RiskCalculator()
_alert_manager = AlertManager()


@router.get("/positions/summary", summary="获取持仓汇总")
async def get_positions_summary():
    """
    获取当前所有持仓的汇总信息及预警状态
    """
    try:
        summary = _position_monitor.get_portfolio_summary()
        return {
            "success": True,
            "data": summary,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取持仓汇总失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/positions/update", summary="更新持仓数据")
async def update_positions(
    positions: Dict[str, Dict[str, float]],
    prices: Dict[str, float],
    sector_map: Optional[Dict[str, str]] = None
):
    """
    更新持仓数据并触发风控检查
    
    Args:
        positions: {symbol: {quantity, avg_price}}
        prices: {symbol: current_price}
        sector_map: {symbol: sector_name} 可选
    """
    try:
        updated = _position_monitor.update_positions(positions, prices, sector_map)
        alerts = _position_monitor.check_all()
        
        return {
            "success": True,
            "positions_updated": len(updated),
            "alerts_count": len(alerts),
            "alerts": [
                {
                    "level": a.level.value,
                    "code": a.code,
                    "message": a.message,
                    "symbol": a.symbol
                }
                for a in alerts
            ],
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"更新持仓失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk/assessment", summary="获取风险评估报告")
async def get_risk_assessment(
    positions: Dict[str, float] = Body(..., description="{symbol: market_value}"),
    cash: float = Query(0, description="现金余额"),
    returns_json: Optional[str] = Query(None, description="收益率JSON数组")
):
    """
    获取完整风险评估报告
    """
    try:
        import json as json_lib
        
        returns = None
        if returns_json:
            try:
                returns = json_lib.loads(returns_json)
                import numpy as np
                returns = np.array(returns)
            except:
                pass
        
        import numpy as np
        equity = None
        if returns is not None:
            equity = np.cumprod(1 + returns) * (sum(positions.values()) + cash)
        
        report = _risk_calculator.full_risk_assessment(
            positions=positions,
            cash=cash,
            returns=returns,
            equity_curve=equity
        )
        
        return {
            "success": True,
            "data": report,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取风险评估失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/send", summary="手动触发预警")
async def send_manual_alert(
    level: str = Query(..., description="预警级别 INFO/WARNING/ERROR/CRITICAL"),
    code: str = Query(..., description="预警代码"),
    message: str = Query(..., description="预警消息"),
    symbol: Optional[str] = Query(None, description="涉及标的")
):
    """手动发送一条预警"""
    try:
        _alert_manager.send(level.upper(), code, message, symbol)
        return {
            "success": True,
            "message": "预警已发送",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"发送预警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/history", summary="查询预警历史")
async def get_alert_history(
    level: Optional[str] = Query(None, description="按级别筛选"),
    symbol: Optional[str] = Query(None, description="按标的筛选"),
    limit: int = Query(100, description="返回条数", le=500)
):
    """查询预警历史记录"""
    try:
        history = _alert_manager.get_alert_history(level, symbol, limit)
        return {
            "success": True,
            "data": history,
            "count": len(history),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"查询预警历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/thresholds", summary="获取风控阈值配置")
async def get_risk_thresholds():
    """获取当前风控阈值配置"""
    return {
        "success": True,
        "data": _position_monitor.t,
        "timestamp": datetime.now()
    }


@router.put("/alerts/thresholds", summary="更新风控阈值")
async def update_risk_thresholds(
    thresholds: Dict[str, float]
):
    """更新风控阈值"""
    try:
        valid_keys = list(_position_monitor.DEFAULTS.keys())
        invalid = [k for k in thresholds if k not in valid_keys]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"无效的阈值键: {invalid}，有效键: {valid_keys}"
            )
        
        _position_monitor.t.update(thresholds)
        return {
            "success": True,
            "message": "阈值已更新",
            "thresholds": _position_monitor.t,
            "timestamp": datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新阈值失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/config", summary="配置预警通道")
async def config_alert_channel(
    channels: List[str] = Query(..., description="通道列表: log/webhook/file/console"),
    webhook_url: Optional[str] = Query(None, description="Webhook URL"),
    alert_file: Optional[str] = Query(None, description="预警文件路径")
):
    """配置预警通道"""
    try:
        config = {
            "channels": channels,
            "webhook_url": webhook_url,
            "alert_file": alert_file or "logs/alerts.json"
        }
        _alert_manager.config = config
        _alert_manager.channels = channels
        _alert_manager.webhook_url = webhook_url
        _alert_manager.alert_file = alert_file or _alert_manager.alert_file
        
        return {
            "success": True,
            "message": "预警通道已配置",
            "config": config,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"配置预警通道失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

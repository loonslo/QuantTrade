# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) 服务
统一管理大模型API的调用和分析
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from utils.core.logger_manager import get_logger
from data.models.mcp import (
    MCPAnalysisRequest, MCPAnalysisResult,
    MarketTrendAnalysis, RiskAssessment, TradingSignal,
    MCPAnalysisResponse, MCPStatusResponse
)
from config.python.mcp_config import MCPConfig
from services.llm import llm_manager

class MCPService:
    """MCP服务主类 - 统一管理大模型调用"""

    def __init__(self):
        self.logger = get_logger("api.mcp_service")

        # 加载配置
        self.config = MCPConfig()

        # 验证配置
        if not self.config.validate_config():
            self.logger.warning("MCP配置验证失败，使用默认配置")

        # 初始化LLM管理器
        self.llm_manager = llm_manager

        self.logger.info(f"MCP服务初始化完成，可用大模型: {self.llm_manager.get_available_providers()}")

    async def analyze_data(
        self,
        request: MCPAnalysisRequest
    ) -> MCPAnalysisResponse:
        """
        使用大模型进行数据分析

        Args:
            request: MCP分析请求

        Returns:
            MCP分析响应
        """
        try:
            self.logger.info(f"使用大模型进行数据分析 {request.request_id}")

            # 确定使用的LLM提供者
            provider_name = self._determine_llm_provider(request)

            # 构建数据帧
            data_frames = self._build_data_frames(request)

            # 调用LLM管理器进行分析
            llm_result = await self.llm_manager.analyze_with_llm(
                data_frames=data_frames,
                analysis_type=request.analysis_type,
                provider_name=provider_name,
                custom_prompt=request.analysis_parameters.get("custom_prompt") if request.analysis_parameters else None,
                fallback_providers=self._get_fallback_providers(provider_name)
            )

            if llm_result["success"]:
                # 构建MCP分析结果
                mcp_result = self._build_mcp_result(llm_result, request)

                return MCPAnalysisResponse(
                    success=True,
                    data=mcp_result,
                    message=f"大模型分析完成，使用提供者: {llm_result['provider']}"
                )
            else:
                return MCPAnalysisResponse(
                    success=False,
                    data=None,
                    message=f"大模型分析失败: {llm_result.get('error', 'unknown error')}",
                    error_code="LLM_ANALYSIS_ERROR"
                )

        except Exception as e:
            self.logger.error(f"大模型分析失败: {str(e)}")
            return MCPAnalysisResponse(
                success=False,
                data=None,
                message=f"大模型分析失败: {str(e)}",
                error_code="MCP_SERVICE_ERROR"
            )

    def _determine_llm_provider(self, request: MCPAnalysisRequest) -> Optional[str]:
        """确定使用的LLM提供者"""
        # 从请求参数中获取
        if request.analysis_parameters:
            provider = request.analysis_parameters.get("llm_provider")
            if provider and provider in self.llm_manager.get_available_providers():
                return provider

        # 从配置中获取默认提供者
        if hasattr(self.config, 'default_llm_provider'):
            return self.config.default_llm_provider

        # 使用LLM管理器的默认提供者
        return self.llm_manager.default_provider

    def _get_fallback_providers(self, primary_provider: Optional[str]) -> List[str]:
        """获取备用提供者列表"""
        available_providers = self.llm_manager.get_available_providers()

        # 排除主提供者
        fallback = [p for p in available_providers if p != primary_provider]

        # 优先使用SiliconFlow作为备用
        if "siliconflow" in fallback:
            fallback.remove("siliconflow")
            fallback.insert(0, "siliconflow")

        return fallback

    def _build_data_frames(self, request: MCPAnalysisRequest) -> List[Dict[str, Any]]:
        """构建数据帧列表"""
        data_frames = []

        if request.data_frames:
            for frame in request.data_frames:
                frame_type_value = None
                try:
                    ft = getattr(frame, 'frame_type', None)
                    frame_type_value = ft.value if hasattr(ft, 'value') else str(ft)
                except Exception:
                    frame_type_value = "unknown"
                data_frame = {
                    "frame_type": frame_type_value,
                    "data": frame.data,
                    "symbol": getattr(frame, 'symbol', None),
                    "timeframe": getattr(frame, 'timeframe', None),
                    "timestamp": getattr(frame, 'timestamp', None)
                }
                data_frames.append(data_frame)

        return data_frames

    def _build_mcp_result(self, llm_result: Dict[str, Any], request: MCPAnalysisRequest) -> MCPAnalysisResult:
        """构建MCP分析结果"""
        # 解析LLM分析结果
        analysis = llm_result.get("analysis", {})

        # 根据分析类型构建结果
        if request.analysis_type == "market_trend":
            result = MarketTrendAnalysis(
                trend_direction=analysis.get("trend_direction", "unknown"),
                trend_strength=analysis.get("trend_strength", "unknown"),
                support_levels=analysis.get("support_levels", []),
                resistance_levels=analysis.get("resistance_levels", []),
                confidence_score=analysis.get("confidence_score", 0.0),
                analysis_text=llm_result.get("raw_response", ""),
                provider=llm_result.get("provider", "unknown"),
                model=llm_result.get("model", "unknown")
            )
        elif request.analysis_type == "risk_assessment":
            result = RiskAssessment(
                risk_level=analysis.get("risk_level", "unknown"),
                risk_factors=analysis.get("risk_factors", []),
                volatility_analysis=analysis.get("volatility_analysis", ""),
                drawdown_risk=analysis.get("drawdown_risk", ""),
                risk_management_suggestions=analysis.get("risk_management_suggestions", []),
                analysis_text=llm_result.get("raw_response", ""),
                provider=llm_result.get("provider", "unknown"),
                model=llm_result.get("model", "unknown")
            )
        elif request.analysis_type == "trading_signals":
            result = TradingSignal(
                signal_type=analysis.get("signal_type", "unknown"),
                signal_strength=analysis.get("signal_strength", "unknown"),
                entry_price=analysis.get("entry_price", 0.0),
                stop_loss=analysis.get("stop_loss", 0.0),
                take_profit=analysis.get("take_profit", 0.0),
                confidence_score=analysis.get("confidence_score", 0.0),
                analysis_text=llm_result.get("raw_response", ""),
                provider=llm_result.get("provider", "unknown"),
                model=llm_result.get("model", "unknown")
            )
        else:
            # 综合分析
            result = MCPAnalysisResult(
                analysis_type=request.analysis_type,
                summary=analysis.get("summary", ""),
                key_insights=analysis.get("key_insights", []),
                recommendations=analysis.get("recommendations", []),
                analysis_text=llm_result.get("raw_response", ""),
                provider=llm_result.get("provider", "unknown"),
                model=llm_result.get("model", "unknown")
            )

        return result

    async def check_external_mcp_status(self) -> bool:
        """检查MCP服务状态"""
        try:
            # 测试所有LLM提供者
            connection_results = await self.llm_manager.test_all_connections()

            # 只要有一个提供者可用，服务就正常
            return any(connection_results.values())

        except Exception as e:
            self.logger.error(f"检查MCP服务状态失败: {str(e)}")
            return False

    def get_status(self) -> MCPStatusResponse:
        """获取服务状态"""
        return MCPStatusResponse(
            service_name="Multi-LLM MCPService",
            status="running",
            uptime=time.time(),
            version="2.0.0",
            external_service_url="Multiple LLM APIs",
            external_service_status="unknown"  # 需要异步检查
        )

    async def get_detailed_status(self) -> Dict[str, Any]:
        """获取详细状态信息"""
        # 测试所有LLM提供者连接
        connection_results = await self.llm_manager.test_all_connections()

        # 获取提供者信息
        available_providers = self.llm_manager.get_available_providers()
        provider_details = {}

        for name in available_providers:
            provider = self.llm_manager.get_provider(name)
            if provider:
                provider_details[name] = {
                    "status": "healthy" if connection_results.get(name, False) else "unhealthy",
                    "model_info": provider.get_model_info(),
                    "last_error": provider.get_last_error()
                }

        return {
            "service_name": "Multi-LLM MCPService",
            "status": "running",
            "uptime": time.time(),
            "version": "2.0.0",
            "llm_providers": provider_details,
            "default_provider": self.llm_manager.default_provider,
            "total_providers": len(self.llm_manager.providers),
            "available_providers": len(available_providers),
            "last_connection_check": datetime.now().isoformat()
        }

    async def get_llm_providers_info(self) -> Dict[str, Any]:
        """获取所有LLM提供者信息"""
        providers_info = {}

        for name, provider in self.llm_manager.providers.items():
            providers_info[name] = {
                "name": name,
                "model_info": provider.get_model_info(),
                "is_available": provider.is_service_available(),
                "last_error": provider.get_last_error()
            }

        return {
            "providers": providers_info,
            "default_provider": self.llm_manager.default_provider,
            "available_count": len(self.llm_manager.get_available_providers())
        }

    async def test_specific_provider(self, provider_name: str) -> Dict[str, Any]:
        """测试特定LLM提供者"""
        provider = self.llm_manager.get_provider(provider_name)
        if not provider:
            return {
                "success": False,
                "error": f"提供者{provider_name} 不存在"
            }

        try:
            is_connected = await provider.test_connection()
            return {
                "success": True,
                "provider": provider_name,
                "connected": is_connected,
                "status": "healthy" if is_connected else "unhealthy",
                "last_error": provider.get_last_error()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": provider_name
            }

    async def close(self):
        """关闭服务"""
        await self.llm_manager.close()
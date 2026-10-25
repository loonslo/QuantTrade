# -*- coding: utf-8 -*-
"""
QDII基金数据ORM服务
处理场内QDII基金数据
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import desc, and_

from services.orm.base_orm_service import BaseORMService
from data.models.market_data.qdii_fund_model import QDIIFund
from utils.time.timestamp_utils import TimestampConverter


class QDIIFundServiceORM(BaseORMService):
    """QDII基金ORM服务"""

    def __init__(self):
        super().__init__('qdii_fund_service_orm', QDIIFund)

    async def _execute_sync(self):
        """执行同步任务"""
        self.logger.info("QDII基金数据同步任务执行")
        pass

    def get_task_config(self) -> Dict[str, Any]:
        """获取任务配置"""
        return {
            "task_name": "qdii_fund_sync",
            "description": "QDII基金数据同步",
            "enabled": True
        }

    def save_fund_data(self, fund_data: Dict[str, Any]) -> bool:
        """
        保存基金数据到数据库

        Args:
            fund_data: 基金数据字典

        Returns:
            bool: 保存是否成功
        """
        try:
            fund_code = fund_data.get('fund_code')
            if not fund_code:
                self.logger.error("基金代码不能为空")
                return False

            # 先标记该基金的现有数据为无效
            self.mark_invalid_by_conditions({"fund_code": fund_code, "is_valid": True})

            # 准备记录数据
            current_time = TimestampConverter.get_current_datetime_for_db()
            
            # 确定基金类型
            fund_name = fund_data.get('fund_name', '')
            fund_type = 'OTHER'
            if '纳斯达克' in fund_name or 'NASDAQ' in fund_name.upper():
                fund_type = 'NASDAQ'
            elif '标普' in fund_name or 'S&P' in fund_name.upper() or '500' in fund_name:
                fund_type = 'SP500'
            
            # 处理成立日期
            establishment_date = fund_data.get('establishment_date')
            if isinstance(establishment_date, str):
                try:
                    establishment_date = datetime.strptime(establishment_date, '%Y-%m-%d').date()
                except:
                    establishment_date = None
            
            record_data = {
                "fund_code": fund_code,
                "fund_name": fund_data.get("fund_name", ""),
                "establishment_date": establishment_date,
                "asset_scale": fund_data.get("asset_scale"),
                "net_value": fund_data.get("net_value", 0),
                "accumulated_value": fund_data.get("accumulated_value"),
                "change_percent": fund_data.get("change_percent", 0),
                "purchase_fee": fund_data.get("purchase_fee"),
                "management_fee": fund_data.get("management_fee"),
                "custodian_fee": fund_data.get("custodian_fee"),
                "sales_service_fee": fund_data.get("sales_service_fee"),
                "total_fee": fund_data.get("total_fee"),
                "benchmark": fund_data.get("benchmark"),
                "trading_status": fund_data.get("trading_status", "正常"),
                "purchase_limit": fund_data.get("purchase_limit"),
                "tracking_error": fund_data.get("tracking_error"),
                "fund_type": fund_type,
                "data_timestamp": fund_data.get('updated_at', current_time),
                "is_valid": True,
                "source": fund_data.get("source", "eastmoney")
            }

            # 创建记录
            result = self.create_model_record(record_data)

            if result:
                self.logger.info(f"基金 {fund_code} ({fund_data.get('fund_name')}) 数据保存成功")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"保存基金数据失败: {e}")
            return False

    def save_multiple_funds(self, funds_data: List[Dict[str, Any]]) -> int:
        """
        批量保存基金数据

        Args:
            funds_data: 基金数据列表

        Returns:
            int: 成功保存的数量
        """
        success_count = 0
        for fund_data in funds_data:
            if self.save_fund_data(fund_data):
                success_count += 1
        
        self.logger.info(f"批量保存基金数据完成: {success_count}/{len(funds_data)}")
        return success_count

    def get_latest_fund(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """
        获取最新的基金数据

        Args:
            fund_code: 基金代码

        Returns:
            基金数据字典或None
        """
        try:
            records = self.get_model_records_by_conditions(
                conditions={"fund_code": fund_code, "is_valid": True},
                limit=1,
                order_by="data_timestamp"
            )

            if records:
                record = records[0]
                return self._record_to_dict(record)

            return None

        except Exception as e:
            self.logger.error(f"获取最新基金数据失败: {e}")
            return None

    def get_funds_by_type(self, fund_type: str) -> List[Dict[str, Any]]:
        """
        根据类型获取基金列表

        Args:
            fund_type: 基金类型 (NASDAQ/SP500)

        Returns:
            基金数据列表
        """
        try:
            records = self.get_model_records_by_conditions(
                conditions={"fund_type": fund_type, "is_valid": True},
                order_by="data_timestamp"
            )

            return [self._record_to_dict(record) for record in records]

        except Exception as e:
            self.logger.error(f"获取基金列表失败: {e}")
            return []

    def get_all_latest_funds(self) -> List[Dict[str, Any]]:
        """获取所有最新的基金数据"""
        try:
            # 获取所有有效的基金代码
            session = self.get_session()
            try:
                fund_codes = session.query(QDIIFund.fund_code).filter(
                    QDIIFund.is_valid == True
                ).distinct().all()
                
                results = []
                for (fund_code,) in fund_codes:
                    fund_data = self.get_latest_fund(fund_code)
                    if fund_data:
                        results.append(fund_data)
                
                return results
                
            finally:
                session.close()

        except Exception as e:
            self.logger.error(f"获取所有基金数据失败: {e}")
            return []

    def _record_to_dict(self, record: QDIIFund) -> Dict[str, Any]:
        """将数据库记录转换为字典"""
        return {
            "fund_code": record.fund_code,
            "fund_name": record.fund_name,
            "establishment_date": record.establishment_date.isoformat() if record.establishment_date else None,
            "asset_scale": record.asset_scale,
            "net_value": record.net_value,
            "accumulated_value": record.accumulated_value,
            "change_percent": record.change_percent,
            "purchase_fee": record.purchase_fee,
            "management_fee": record.management_fee,
            "custodian_fee": record.custodian_fee,
            "sales_service_fee": record.sales_service_fee,
            "total_fee": record.total_fee,
            "benchmark": record.benchmark,
            "trading_status": record.trading_status,
            "purchase_limit": record.purchase_limit,
            "tracking_error": record.tracking_error,
            "fund_type": record.fund_type,
            "timestamp": record.data_timestamp,
            "source": record.source
        }


# 单例模式
_qdii_fund_service_instance = None


def get_qdii_fund_service_orm() -> QDIIFundServiceORM:
    """获取QDII基金服务单例"""
    global _qdii_fund_service_instance
    if _qdii_fund_service_instance is None:
        _qdii_fund_service_instance = QDIIFundServiceORM()
    return _qdii_fund_service_instance

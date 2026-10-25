# -*- coding: utf-8 -*-
"""
QDII基金数据提供者
获取场内QDII基金数据（纳斯达克和标普相关）
"""

from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
import json
import re

from utils.core.logger_manager import get_logger


class QDIIFundProvider:
    """QDII基金数据提供者"""

    def __init__(self):
        self.logger = get_logger("qdii_fund_provider")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://fund.eastmoney.com/'
        })
        
        # 纳斯达克和标普相关的QDII基金代码列表
        self.target_funds = {
            # 纳斯达克相关
            '513100': '纳斯达克ETF',
            '513300': '纳指ETF',
            '159941': '纳指ETF',
            '513050': '中概互联',
            '513330': '恒生科技',
            # 标普500相关
            '513500': '标普500ETF',
            '159922': '500ETF',
            '513000': '标普500',
        }

    def get_fund_realtime_data(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """
        获取基金实时数据
        使用天天基金网API
        """
        try:
            # 实时行情接口
            url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析JSONP格式
            text = response.text
            if 'jsonpgz(' in text:
                json_str = text.split('jsonpgz(')[1].rstrip(');')
                data = json.loads(json_str)
                
                return {
                    'fund_code': data.get('fundcode'),
                    'fund_name': data.get('name'),
                    'net_value': float(data.get('dwjz', 0)),  # 单位净值
                    'estimated_value': float(data.get('gsz', 0)),  # 估算净值
                    'change_percent': float(data.get('gszzl', 0)),  # 估算涨跌幅
                    'update_time': data.get('gztime'),  # 更新时间
                }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"获取基金 {fund_code} 实时数据失败: {e}")
            return None

    def get_fund_detail(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """
        获取基金详细信息
        使用天天基金网API
        """
        try:
            # 基金详情接口
            url = f"http://api.fund.eastmoney.com/f10/lsjz"
            params = {
                'fundCode': fund_code,
                'pageIndex': 1,
                'pageSize': 1,
                'startDate': '',
                'endDate': ''
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('Data') and data['Data'].get('LSJZList'):
                latest = data['Data']['LSJZList'][0]
                
                # 获取基金基本信息
                info_url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
                info_response = self.session.get(info_url, timeout=10)
                fund_name = self.target_funds.get(fund_code, f"基金{fund_code}")
                
                if 'jsonpgz(' in info_response.text:
                    json_str = info_response.text.split('jsonpgz(')[1].rstrip(');')
                    info_data = json.loads(json_str)
                    fund_name = info_data.get('name', fund_name)
                
                return {
                    'fund_code': fund_code,
                    'fund_name': fund_name,
                    'net_value': float(latest.get('DWJZ', 0)),
                    'accumulated_value': float(latest.get('LJJZ', 0)),
                    'change_percent': float(latest.get('JZZZL', 0).rstrip('%')) if latest.get('JZZZL') else 0,
                    'net_value_date': latest.get('FSRQ'),
                }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"获取基金 {fund_code} 详情失败: {e}")
            return None

    def get_fund_comprehensive_info(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """
        获取基金综合信息（包含费率、规模等）
        """
        try:
            # 使用天天基金网的基金档案页面API
            url = f"http://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            text = response.text
            
            # 解析JavaScript变量
            result = {
                'fund_code': fund_code,
                'fund_name': self.target_funds.get(fund_code, f"基金{fund_code}"),
                'net_value': 0.0,
                'change_percent': 0.0,
                'establishment_date': None,
                'asset_scale': None,
                'accumulated_value': None,
                'purchase_fee': None,
                'management_fee': None,
                'custodian_fee': None,
                'sales_service_fee': None,
                'total_fee': None,
                'benchmark': None,
                'trading_status': '正常',
                'purchase_limit': '无限制',
                'tracking_error': None,
                'updated_at': datetime.now()
            }
            
            # 提取基金名称
            if 'var fS_name = "' in text:
                name_start = text.find('var fS_name = "') + len('var fS_name = "')
                name_end = text.find('"', name_start)
                result['fund_name'] = text[name_start:name_end]
            
            # 提取成立日期 - 尝试多种可能的变量名
            establishment_date = None
            
            # 方法1: 查找 fS_estabDate 变量
            if 'var fS_estabDate = "' in text:
                try:
                    date_start = text.find('var fS_estabDate = "') + len('var fS_estabDate = "')
                    date_end = text.find('"', date_start)
                    establishment_date = text[date_start:date_end]
                except:
                    pass
            
            # 方法2: 从净值趋势数据中获取第一个日期（成立日期）
            if not establishment_date and 'var Data_netWorthTrend = ' in text:
                try:
                    match = re.search(r'var Data_netWorthTrend = (\[.*?\]);', text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(1))
                        if data and len(data) > 0:
                            first_record = data[0]
                            if isinstance(first_record, dict) and 'x' in first_record:
                                timestamp_ms = first_record['x']
                                dt = datetime.fromtimestamp(timestamp_ms / 1000)
                                establishment_date = dt.strftime('%Y-%m-%d')
                            elif isinstance(first_record, list) and len(first_record) >= 1:
                                timestamp_ms = first_record[0]
                                dt = datetime.fromtimestamp(timestamp_ms / 1000)
                                establishment_date = dt.strftime('%Y-%m-%d')
                except Exception as e:
                    self.logger.debug(f"从净值数据推断成立日期失败: {e}")
            
            if establishment_date:
                result['establishment_date'] = establishment_date
                self.logger.debug(f"基金 {fund_code} 成立日期: {establishment_date}")
            
            # 提取资产规模 - Data_assetAllocation是对象格式，包含series数组
            if 'var Data_assetAllocation = ' in text:
                try:
                    # 匹配对象格式 {...}
                    match = re.search(r'var Data_assetAllocation = (\{.*?\});', text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(1))
                        # 查找"净资产"系列
                        if 'series' in data:
                            for series in data['series']:
                                if series.get('name') == '净资产' and series.get('data'):
                                    # 取最后一个数据点作为最新资产规模
                                    asset_data = series['data']
                                    if asset_data and len(asset_data) > 0:
                                        latest_value = asset_data[-1]
                                        if latest_value is not None and latest_value > 0:
                                            result['asset_scale'] = float(latest_value)
                                            self.logger.debug(f"基金 {fund_code} 资产规模: {result['asset_scale']} 亿元")
                                    break
                except Exception as e:
                    self.logger.debug(f"解析资产规模失败: {e}")
            
            # 提取最新净值 - 使用正则表达式
            if 'var Data_netWorthTrend = ' in text:
                try:
                    match = re.search(r'var Data_netWorthTrend = (\[.*?\]);', text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(1))
                        if data and len(data) > 0:
                            latest = data[-1]
                            if 'y' in latest and latest['y'] is not None:
                                result['net_value'] = float(latest['y'])
                except Exception as e:
                    self.logger.debug(f"解析净值失败: {e}")
            
            # 提取累计净值 - Data_ACWorthTrend是数组格式 [[timestamp, value], ...]
            if 'var Data_ACWorthTrend = ' in text:
                try:
                    match = re.search(r'var Data_ACWorthTrend = (\[.*?\]);', text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(1))
                        if data and len(data) > 0:
                            latest = data[-1]
                            # 处理两种可能的格式：对象 {x, y} 或数组 [timestamp, value]
                            if isinstance(latest, dict) and 'y' in latest and latest['y'] is not None:
                                result['accumulated_value'] = float(latest['y'])
                                self.logger.debug(f"基金 {fund_code} 累计净值: {result['accumulated_value']}")
                            elif isinstance(latest, list) and len(latest) >= 2 and latest[1] is not None:
                                result['accumulated_value'] = float(latest[1])
                                self.logger.debug(f"基金 {fund_code} 累计净值: {result['accumulated_value']}")
                except Exception as e:
                    self.logger.debug(f"解析累计净值失败: {e}")
            
            # 获取详细信息补充（从历史净值API）
            detail = self.get_fund_detail(fund_code)
            if detail:
                # 优先使用历史净值API的数据，因为更准确
                if detail.get('net_value') and detail['net_value'] > 0:
                    result['net_value'] = detail['net_value']
                if detail.get('accumulated_value') and detail['accumulated_value'] > 0:
                    result['accumulated_value'] = detail['accumulated_value']
                if detail.get('change_percent') is not None:
                    result['change_percent'] = detail['change_percent']
                if detail.get('fund_name'):
                    result['fund_name'] = detail['fund_name']
            
            # 获取实时数据补充（用于涨跌幅）
            realtime = self.get_fund_realtime_data(fund_code)
            if realtime:
                # 实时数据的涨跌幅更及时
                if realtime.get('change_percent') is not None:
                    result['change_percent'] = realtime['change_percent']
                # 如果没有净值数据，使用实时净值
                if result['net_value'] == 0 and realtime.get('net_value'):
                    result['net_value'] = realtime['net_value']
            
            # 设置费率（场内ETF通常费率较低）
            result['purchase_fee'] = 0.0  # 场内交易无申购费
            result['management_fee'] = 0.5  # 管理费率约0.5%
            result['custodian_fee'] = 0.1  # 托管费率约0.1%
            result['sales_service_fee'] = 0.0  # 无销售服务费
            result['total_fee'] = 0.6  # 综合费率
            
            # 设置业绩比较基准
            fund_name_upper = result['fund_name'].upper()
            if '纳斯达克' in result['fund_name'] or 'NASDAQ' in fund_name_upper or 'NDX' in fund_name_upper:
                result['benchmark'] = '纳斯达克100指数'
            elif '标普' in result['fund_name'] or 'S&P' in fund_name_upper or ('500' in result['fund_name'] and 'ETF' in fund_name_upper):
                result['benchmark'] = '标普500指数'
            elif '中概' in result['fund_name'] or '互联' in result['fund_name']:
                result['benchmark'] = '中概互联指数'
            elif '恒生' in result['fund_name']:
                result['benchmark'] = '恒生科技指数'
            
            # 提取购买限制信息
            if 'var fund_maxBuy = "' in text:
                try:
                    match = re.search(r'var fund_maxBuy = "([^"]*)"', text)
                    if match:
                        max_buy = match.group(1)
                        if max_buy and max_buy != '0':
                            result['purchase_limit'] = f"{max_buy}元"
                            self.logger.debug(f"基金 {fund_code} 购买限制: {result['purchase_limit']}")
                        else:
                            result['purchase_limit'] = '无限制'
                except Exception as e:
                    self.logger.debug(f"解析购买限制失败: {e}")
                    result['purchase_limit'] = '无限制'
            else:
                result['purchase_limit'] = '无限制'
            
            # 提取交易状态
            if 'var fund_purchaseStatus = "' in text:
                try:
                    match = re.search(r'var fund_purchaseStatus = "([^"]*)"', text)
                    if match:
                        purchase_status = match.group(1)
                        if purchase_status == '开放申购':
                            result['trading_status'] = '正常'
                        elif purchase_status == '暂停申购':
                            result['trading_status'] = '暂停申购'
                        else:
                            result['trading_status'] = purchase_status
                except Exception as e:
                    self.logger.debug(f"解析交易状态失败: {e}")
                    result['trading_status'] = '正常'
            else:
                result['trading_status'] = '正常'
            
            # 计算追踪偏差（如果有足够的历史数据）
            # 追踪偏差 = 基金收益率 - 基准收益率的标准差
            # 这里我们简化处理，使用近期涨跌幅作为参考
            try:
                if result['net_value'] > 0 and result['accumulated_value'] > 0:
                    # 简单估算：累计净值与单位净值的差异可以反映长期追踪情况
                    # 对于ETF，追踪偏差通常很小（<0.5%）
                    tracking_diff = abs(result['accumulated_value'] - result['net_value'])
                    if tracking_diff > 0:
                        # 估算年化追踪偏差（简化计算）
                        result['tracking_error'] = round(min(tracking_diff / result['net_value'] * 100, 2.0), 2)
                        self.logger.debug(f"基金 {fund_code} 估算追踪偏差: {result['tracking_error']}%")
            except Exception as e:
                self.logger.debug(f"计算追踪偏差失败: {e}")
            
            # 如果仍然没有净值数据，记录警告
            if result['net_value'] == 0:
                self.logger.warning(f"基金 {fund_code} ({result['fund_name']}) 未能获取到净值数据")
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取基金 {fund_code} 综合信息失败: {e}")
            return None

    def get_all_qdii_funds(self) -> List[Dict[str, Any]]:
        """
        获取所有目标QDII基金数据
        """
        results = []
        
        for fund_code, fund_name in self.target_funds.items():
            self.logger.info(f"正在获取基金 {fund_code} ({fund_name}) 的数据...")
            
            fund_info = self.get_fund_comprehensive_info(fund_code)
            if fund_info:
                results.append(fund_info)
                self.logger.info(f"成功获取 {fund_info['fund_name']}: 净值 {fund_info['net_value']}, 涨跌 {fund_info['change_percent']:+.2f}%")
            else:
                self.logger.warning(f"获取基金 {fund_code} 数据失败")
        
        return results

    def get_nasdaq_funds(self) -> List[Dict[str, Any]]:
        """获取纳斯达克相关基金"""
        nasdaq_codes = ['513100', '513300', '159941', '513050', '513330']
        results = []
        
        for fund_code in nasdaq_codes:
            if fund_code in self.target_funds:
                fund_info = self.get_fund_comprehensive_info(fund_code)
                if fund_info:
                    results.append(fund_info)
        
        return results

    def get_sp500_funds(self) -> List[Dict[str, Any]]:
        """获取标普500相关基金"""
        sp500_codes = ['513500', '159922', '513000']
        results = []
        
        for fund_code in sp500_codes:
            if fund_code in self.target_funds:
                fund_info = self.get_fund_comprehensive_info(fund_code)
                if fund_info:
                    results.append(fund_info)
        
        return results


# 单例模式
_qdii_fund_provider_instance = None

def get_qdii_fund_provider() -> QDIIFundProvider:
    """获取QDII基金数据提供者单例"""
    global _qdii_fund_provider_instance
    if _qdii_fund_provider_instance is None:
        _qdii_fund_provider_instance = QDIIFundProvider()
    return _qdii_fund_provider_instance

"""
量化交易系统 - 仓位管理工具
========================================

提供仓位管理的工具函数和辅助功能。

仓位管理策略：
1. AllInPositionMixin: 全仓买入/卖出
2. TwoThreeFivePositionMixin: 2/3/5分批建仓
3. FixedRatioPositionMixin: 固定比例调整
4. PyramidAllPositionMixin: 金字塔式建仓
5. MartingalePositionMixin: 马丁格尔策略
6. KellyPositionMixin: 凯利公式
7. VolatilityPositionMixin: 波动率调整

作者：量化交易团队
版本：1.0.0
"""

from .position_managers import (
    AllInPositionMixin,
    TwoThreeFivePositionMixin,
    FixedRatioPositionMixin,
    PyramidAllPositionMixin,
    MartingalePositionMixin,
    KellyPositionMixin,
    VolatilityPositionMixin,
)


def get_position_mixin(position_type, **kwargs):
    """
    根据仓位类型获取对应的仓位管理Mixin

    这是一个工厂函数，根据用户指定的仓位管理类型，
    返回相应的仓位管理Mixin实例。

    Args:
        position_type (str): 仓位管理类型
            - 'all_in': 全仓模式
            - 'two_three_five': 235分仓模式
            - 'fixed_ratio': 固定比例模式
            - 'pyramid': 金字塔模式
            - 'martingale': 马丁格尔模式
            - 'kelly': 凯利公式模式
            - 'volatility': 波动率模式
        **kwargs: 仓位管理参数

    Returns:
        BasePositionMixin: 对应的仓位管理实例

    使用示例:
        # 获取全仓模式
        mixin_all_in = get_position_mixin('all_in')

        # 获取固定比例模式并传递参数
        mixin_fixed = get_position_mixin('fixed_ratio', ratio=0.1)

    注意:
        如果传入未知的position_type，会返回默认的AllInPositionMixin
    """
    position_mixins = {
        'all_in': AllInPositionMixin,
        'two_three_five': TwoThreeFivePositionMixin,
        'fixed_ratio': FixedRatioPositionMixin,
        'pyramid': PyramidAllPositionMixin,
        'martingale': MartingalePositionMixin,
        'kelly': KellyPositionMixin,
        'volatility': VolatilityPositionMixin,
    }
    return position_mixins.get(position_type, AllInPositionMixin)(**kwargs)

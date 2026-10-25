from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class StandardTradeRecord:
    id: Optional[str]
    datetime: datetime
    symbol: str
    side: str  # 'buy' | 'sell'
    quantity: float
    price: float
    commission: float
    pnl: Optional[float] = None
    cash_before: Optional[float] = None
    cash_after: Optional[float] = None
    position_before: Optional[float] = None
    position_after: Optional[float] = None
    strategy_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # 转换 datetime 为 ISO 字符串，便于 JSON 序列化
        data["datetime"] = self.datetime.isoformat() if isinstance(self.datetime, datetime) else str(self.datetime)
        return data


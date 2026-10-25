"""Convert the documented Backtrader Transactions tuple without price heuristics."""

from datetime import datetime
from typing import Any

from .core_types import StandardTradeRecord


def convert_backtrader_transactions(
    transactions: dict[datetime, list[list]], commission_rate: float,
    symbol_default: str, strategy_name: str | None = None, initial_cash: float = 100000,
) -> list[dict[str, Any]]:
    """Transactions contains [signed_size, price, data_id, symbol, cash_value]."""
    records = []
    inventory: dict[str, tuple[float, float]] = {}
    cash = initial_cash
    for timestamp, entries in sorted(transactions.items()):
        for signed_size, price, _, symbol, _ in entries:
            symbol = symbol or symbol_default
            signed_size, price = float(signed_size), float(price)
            if not signed_size:
                continue
            quantity = abs(signed_size)
            fee = quantity * price * commission_rate
            old_quantity, old_cost = inventory.get(symbol, (0.0, 0.0))
            cash_before = cash
            if signed_size > 0:
                cash -= quantity * price + fee
                inventory[symbol] = (old_quantity + quantity, old_cost + quantity * price + fee)
                pnl = None
            else:
                if quantity > old_quantity + 1e-8:
                    raise ValueError("Long-only transaction history contains an uncovered sell")
                cost = old_cost * quantity / old_quantity
                cash += quantity * price - fee
                pnl = quantity * price - fee - cost
                inventory[symbol] = (max(0.0, old_quantity - quantity), max(0.0, old_cost - cost))
            records.append(StandardTradeRecord(
                id=f"backtest_{len(records)}", datetime=timestamp, symbol=symbol,
                side="buy" if signed_size > 0 else "sell", quantity=quantity, price=price,
                commission=fee, pnl=pnl, cash_before=cash_before, cash_after=cash,
                position_before=old_quantity, position_after=inventory[symbol][0],
                strategy_name=strategy_name,
            ).to_dict())
    return records

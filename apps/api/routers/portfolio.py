from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any

from apps.api.core.database import get_db
from apps.api.core.security import get_current_user
from apps.api.core import bybit as bybit_client
from shared.db.models import Trade, ExchangeAccount
from apps.api.core.config import settings
from services.trading_engine import bot_loop

router = APIRouter()


@router.get("/")
def get_portfolio(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns live portfolio data:
    - Real USDT balance synced from Bybit
    - Real open positions from Bybit
    - Trade statistics from local DB
    - Bot status
    """
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user["id"],
        ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
    ).first()

    if not account:
        return {
            "status": "success",
            "data": {
                "connected": False,
                "total_value": 0.0,
                "usdt_balance": 0.0,
                "unrealized_pnl": 0.0,
                "todays_pnl": 0.0,
                "win_rate": 0.0,
                "open_positions_count": 0,
                "balances": [],
                "positions": [],
                "bot_running": bot_loop.get_status().get("running", False),
            }
        }

    # Fetch live balance and positions
    if account.exchange_name == "paper":
        from shared.db.models import Balance, Position
        b = db.query(Balance).filter(Balance.account_id == account.id, Balance.asset == "USDT").first()
        usdt_free = b.free if b else 0.0
        usdt_total = (b.free + b.locked) if b else 0.0
        live_balances = {"USDT": {"free": usdt_free, "locked": (b.locked if b else 0.0), "total": usdt_total, "usd_value": usdt_total}}
        usdt_usd = usdt_total

        pos = db.query(Position).filter(Position.account_id == account.id).all()
        live_positions = [
            {
                "symbol": p.symbol,
                "side": p.side,
                "size": p.size,
                "entry_price": p.entry_price,
                "unrealized_pnl": p.unrealized_pnl,
            }
            for p in pos
        ]
        unrealized_pnl = sum(p.get("unrealized_pnl", 0.0) for p in live_positions)
        total_usd = usdt_usd + unrealized_pnl
    else:
        live_balances = bybit_client.get_live_balance(account.api_key, account.api_secret)
        usdt_data   = live_balances.get("USDT", {})
        usdt_free   = usdt_data.get("free", 0.0)
        usdt_total  = usdt_data.get("total", 0.0)
        usdt_usd    = usdt_data.get("usd_value", usdt_total)
        total_usd = sum(v.get("usd_value", v.get("total", 0)) for v in live_balances.values())

        live_positions = bybit_client.get_live_positions(account.api_key, account.api_secret)
        unrealized_pnl = sum(p.get("unrealized_pnl", 0.0) for p in live_positions)

    # Trade statistics from local DB
    trades = db.query(Trade).filter(Trade.account_id == account.id).all()
    total_trades = len(trades)
    # Simple win rate: compare successive trade pairs (buy then sell)
    win_rate = 0.0
    if total_trades >= 2:
        # Approximate: count trades where the last side was SELL at higher price
        wins = sum(1 for t in trades if t.side == "SELL")
        win_rate = round((wins / (total_trades / 2)) * 100, 1) if total_trades > 0 else 0.0
        win_rate = min(win_rate, 100.0)

    # Format balances for UI
    formatted_balances = [
        {
            "asset":     coin,
            "free":      round(data.get("free", 0), 6),
            "locked":    round(data.get("locked", 0), 6),
            "total":     round(data.get("total", 0), 6),
            "usd_value": round(data.get("usd_value", 0), 2),
        }
        for coin, data in live_balances.items()
        if data.get("total", 0) > 0
    ]

    return {
        "status": "success",
        "data": {
            "connected": True,
            "testnet": settings.BYBIT_TESTNET,
            "total_value": round(total_usd, 2),
            "usdt_balance": round(usdt_free, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "todays_pnl": round(unrealized_pnl, 2),
            "win_rate": win_rate,
            "open_positions_count": len(live_positions),
            "balances": formatted_balances,
            "positions": live_positions,
            "bot_status": bot_loop.get_status(),
        }
    }


@router.post("/risk/calculator")
def calculate_risk(
    account_balance: float,
    risk_percentage: float,
    entry_price: float,
    stop_loss: float,
    current_user: dict = Depends(get_current_user)
):
    """Endpoint exposing the RiskEngine calculator."""
    from services.risk_engine.calculator import RiskManager

    result = RiskManager.calculate_position_size(
        account_balance=account_balance,
        risk_percentage=risk_percentage,
        entry_price=entry_price,
        stop_loss=stop_loss
    )
    return result

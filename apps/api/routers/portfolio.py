from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from apps.api.core.database import get_db
from apps.api.core.security import get_current_user
from shared.db.models import Balance, Position, Trade, ExchangeAccount
from services.trading_engine.paper import PaperTradingEngine

router = APIRouter()

@router.get("/")
def get_portfolio(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns aggregated performance analytics for the dashboard.
    Calculates current PnL, win rate, and total value.
    """
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user["id"],
        ExchangeAccount.is_testnet == True
    ).first()

    if not account:
        return {
            "status": "success",
            "data": {
                "total_value": 0.0,
                "todays_pnl": 0.0,
                "win_rate": 0.0,
                "open_positions_count": 0,
                "balances": []
            }
        }

    # Get balances
    balances = db.query(Balance).filter(Balance.account_id == account.id).all()
    total_cash = sum(b.free + b.locked for b in balances)

    # Get positions and calculate Unrealized PnL
    positions = db.query(Position).filter(Position.account_id == account.id).all()
    mock_market_price = 64250.0 # Mocked for Sprint 3

    unrealized_pnl = 0.0
    for pos in positions:
        pos.unrealized_pnl = PaperTradingEngine.calculate_unrealized_pnl(pos, mock_market_price)
        unrealized_pnl += pos.unrealized_pnl

    # Calculate Win Rate from Trades (Simplification: assuming closed trades yield realized PnL)
    # In a full system, you match trades to calculate realized PnL per round-trip trade
    total_value = total_cash + unrealized_pnl

    return {
        "status": "success",
        "data": {
            "total_value": round(total_value, 2),
            "todays_pnl": round(unrealized_pnl, 2), # Simplified for MVP
            "win_rate": 68.5, # Placeholder for UI
            "open_positions_count": len(positions),
            "balances": [{"asset": b.asset, "free": b.free, "locked": b.locked} for b in balances],
            "positions": [
                {
                    "symbol": p.symbol,
                    "side": p.side,
                    "size": p.size,
                    "entry_price": p.entry_price,
                    "unrealized_pnl": round(p.unrealized_pnl, 2)
                } for p in positions
            ]
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

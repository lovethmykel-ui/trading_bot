from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from apps.api.core.database import get_db
from apps.api.core.security import get_current_user
from apps.api.core.config import settings
from shared.db.models import (
    ExchangeAccount, Balance, Position, Order, Trade, SystemLog
)
from services.trading_engine import bot_loop

router = APIRouter()


# ---------------------------------------------------------------------------
# Bot control
# ---------------------------------------------------------------------------
@router.post("/start")
async def start_bot(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Start the autonomous trading loop."""
    # Verify there's a connected account
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user["id"],
        ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
    ).first()
    if not account:
        raise HTTPException(
            status_code=400,
            detail="No exchange account connected. Go to Settings and connect your Bybit API keys first."
        )

    started = bot_loop.start_bot()
    if not started:
        return {"status": "already_running", "message": "Bot is already running."}

    return {
        "status": "started",
        "message": f"🤖 Autonomous trading bot started. Scanning market every {5} minutes.",
        "config": {
            "risk_per_trade_pct": 10.0,
            "stop_loss_pct": 2.0,
            "take_profit_pct": 4.0,
            "testnet": True,
        }
    }


@router.post("/stop")
async def stop_bot(current_user: dict = Depends(get_current_user)):
    """Stop the autonomous trading loop."""
    bot_loop.stop_bot()
    return {"status": "stopped", "message": "🛑 Bot has been stopped."}


@router.get("/status")
def get_bot_status(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Returns current bot state, last scan, last trade, last signal."""
    return {"status": "success", "data": bot_loop.get_status()}


# ---------------------------------------------------------------------------
# Data reset
# ---------------------------------------------------------------------------
@router.post("/reset")
async def reset_all_data(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Wipes all local simulation/trading data for a fresh start.
    Does NOT affect your Bybit exchange account.
    """
    # Stop bot if running
    bot_loop.stop_bot()

    try:
        user_id = current_user["id"]

        # Find all accounts for this user
        accounts = db.query(ExchangeAccount).filter(
            ExchangeAccount.user_id == user_id
        ).all()
        account_ids = [a.id for a in accounts]

        # Delete in dependency order
        if account_ids:
            db.query(Trade).filter(Trade.account_id.in_(account_ids)).delete(synchronize_session=False)
            db.query(Order).filter(Order.account_id.in_(account_ids)).delete(synchronize_session=False)
            db.query(Position).filter(Position.account_id.in_(account_ids)).delete(synchronize_session=False)
            db.query(Balance).filter(Balance.account_id.in_(account_ids)).delete(synchronize_session=False)
            db.query(ExchangeAccount).filter(ExchangeAccount.user_id == user_id).delete(synchronize_session=False)

        db.query(SystemLog).delete(synchronize_session=False)
        db.commit()

        return {
            "status": "success",
            "message": "✅ All data wiped. You can now connect your API keys and start fresh."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from apps.api.core.database import get_db
from apps.api.core.security import get_current_user
from apps.api.core import bybit as bybit_client
from shared.db.models import Order, Position, ExchangeAccount
from services.trading_engine.live import LiveTradingEngine
from apps.api.core.config import settings

router = APIRouter()


class OrderCreate(BaseModel):
    symbol: str
    side: str      # "BUY" or "SELL"
    size: float
    order_type: str = "MARKET"
    price: float = None


# ---------------------------------------------------------------------------
# Order history — from local DB (our recorded orders)
# ---------------------------------------------------------------------------
@router.get("/")
def get_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = Query(50)
):
    """Fetch recent orders recorded in local DB."""
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user["id"],
        ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
    ).first()

    if not account:
        return {"status": "success", "data": []}

    orders = (
        db.query(Order)
        .filter(Order.account_id == account.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "status": "success",
        "data": [
            {
                "id":         o.id,
                "symbol":     o.symbol,
                "side":       o.side,
                "order_type": o.order_type,
                "price":      o.price,
                "amount":     o.amount,
                "status":     o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ],
    }


# ---------------------------------------------------------------------------
# Live order history — from Bybit directly
# ---------------------------------------------------------------------------
@router.get("/live/history")
def get_live_order_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50)
):
    """Fetch real order history directly from Bybit."""
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user["id"],
        ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
    ).first()
    if not account:
        raise HTTPException(status_code=400, detail="No exchange account connected.")

    orders = bybit_client.get_order_history(account.api_key, account.api_secret, limit=limit)
    return {"status": "success", "data": orders}


# ---------------------------------------------------------------------------
# Manual live order execution
# ---------------------------------------------------------------------------
@router.post("/live/execute")
def execute_live_trade(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Manually execute a REAL order on Bybit using the connected API keys.
    Automatically calculates SL/TP from configured percentages.
    """
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user["id"],
        ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
    ).first()

    if not account:
        raise HTTPException(
            status_code=400,
            detail="No exchange account connected. Add your API keys in Settings."
        )

    if order_in.order_type.upper() != "MARKET":
        raise HTTPException(status_code=400, detail="Only MARKET orders supported currently.")

    # Get live price for SL/TP calculation
    current_price = bybit_client.get_live_price(order_in.symbol)
    if not current_price:
        raise HTTPException(status_code=503, detail=f"Cannot fetch live price for {order_in.symbol}")

    side_upper = order_in.side.upper()
    if side_upper in ["BUY", "LONG"]:
        sl = current_price * (1 - settings.STOP_LOSS_PCT / 100)
        tp = current_price * (1 + settings.TAKE_PROFIT_PCT / 100)
    else:
        sl = current_price * (1 + settings.STOP_LOSS_PCT / 100)
        tp = current_price * (1 - settings.TAKE_PROFIT_PCT / 100)

    result = LiveTradingEngine.execute_live_order(
        db=db,
        account=account,
        symbol=order_in.symbol,
        side=order_in.side,
        qty=order_in.size,
        stop_loss_price=round(sl, 4),
        take_profit_price=round(tp, 4),
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"status": "success", "data": result}


# ---------------------------------------------------------------------------
# Open positions
# ---------------------------------------------------------------------------
@router.get("/positions")
def get_positions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Returns open positions synced from Bybit."""
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user["id"],
        ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
    ).first()
    if not account:
        return {"status": "success", "data": []}

    positions = bybit_client.get_live_positions(account.api_key, account.api_secret)
    return {"status": "success", "data": positions}

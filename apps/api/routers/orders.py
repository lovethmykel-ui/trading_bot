from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from apps.api.core.database import get_db
from apps.api.core.security import get_current_user
from shared.db.models import Order, Position, ExchangeAccount
from services.trading_engine.paper import PaperTradingEngine

router = APIRouter()

class OrderCreate(BaseModel):
    symbol: str
    side: str
    size: float
    order_type: str = "MARKET"
    price: float = None # Required if order_type is LIMIT

@router.get("/")
def get_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = Query(50)
):
    """Fetch recent orders for the user's paper trading account."""
    # Assuming one paper account per user for now
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user["id"],
        ExchangeAccount.is_testnet == True
    ).first()

    if not account:
        return {"status": "success", "data": []}

    orders = db.query(Order).filter(Order.account_id == account.id).order_by(Order.created_at.desc()).limit(limit).all()
    return {"status": "success", "data": orders}

@router.post("/paper/execute")
def execute_paper_trade(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Execute a manual paper trade via the simulated trading engine.
    """
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user["id"],
        ExchangeAccount.is_testnet == True
    ).first()

    if not account:
        raise HTTPException(status_code=400, detail="No paper trading account found. Please connect one in settings.")

    if order_in.order_type.upper() != "MARKET":
        raise HTTPException(status_code=400, detail="Only MARKET orders are supported in this sprint.")

    # In a real scenario, fetch live price from redis/bybit socket
    # For Sprint 3 simulation, we will use a mocked current price of 64250.0
    mock_market_price = 64250.0

    result = PaperTradingEngine.execute_market_order(
        db=db,
        account_id=account.id,
        symbol=order_in.symbol,
        side=order_in.side,
        size=order_in.size,
        current_market_price=mock_market_price
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"status": "success", "data": result}

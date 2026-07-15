from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from apps.api.core.database import get_db
from apps.api.core.security import get_current_user
from apps.api.core.bybit import test_connection, get_live_balance, scan_market
from apps.api.core.config import settings
from shared.db.models import ExchangeAccount, User, SystemLog

router = APIRouter()


class ExchangeKeys(BaseModel):
    api_key: str = ""
    api_secret: str = ""
    is_testnet: bool = True   # Defaults to testnet; user can switch via UI
    exchange_name: str = "bybit"


# ---------------------------------------------------------------------------
# Connect & save API keys
# ---------------------------------------------------------------------------
@router.post("/connect")
def connect_exchange(
    keys: ExchangeKeys,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Validates the API key against Bybit and saves it to the database.
    On success, returns the live balance.
    """
    if keys.exchange_name != "paper":
        success, detail = test_connection(keys.api_key, keys.api_secret)
        if not success:
            raise HTTPException(status_code=400, detail=f"API connection failed: {detail}")

    # Ensure user record exists (dev fallback)
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        user = User(id=current_user["id"], email="dev@example.com", hashed_password="mocked_password")
        db.add(user)
        db.commit()

    # Save or update keys in DB
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user["id"],
        ExchangeAccount.is_testnet == keys.is_testnet
    ).first()

    if account:
        account.api_key    = keys.api_key
        account.api_secret = keys.api_secret
        account.exchange_name = keys.exchange_name
    else:
        account = ExchangeAccount(
            user_id=current_user["id"],
            exchange_name=keys.exchange_name,
            api_key=keys.api_key,
            api_secret=keys.api_secret,
            is_testnet=keys.is_testnet,
        )
        db.add(account)

    db.commit()
    db.refresh(account)

    # Fetch live balance to confirm connection
    if keys.exchange_name == "paper":
        from shared.db.models import Balance
        b = db.query(Balance).filter(Balance.account_id == account.id, Balance.asset == "USDT").first()
        if not b:
            b = Balance(account_id=account.id, asset="USDT", free=0.0, locked=0.0)
            db.add(b)
            db.commit()
        usdt = {"free": b.free, "total": b.free + b.locked}
    else:
        live_balance = get_live_balance(keys.api_key, keys.api_secret)
        usdt = live_balance.get("USDT", {})

    # Log the connection event
    try:
        db.add(SystemLog(
            level="INFO",
            component="exchange",
            message=f"API keys connected ({'Testnet' if keys.is_testnet else 'Mainnet'}). "
                    f"USDT balance: ${usdt.get('free', 0):.2f}",
            details={"account_id": account.id, "testnet": keys.is_testnet}
        ))
        db.commit()
    except Exception:
        pass

    return {
        "status": "success",
        "message": f"{'Testnet' if keys.is_testnet else 'Mainnet'} connection established and saved!",
        "balance": {
            "usdt_free":  round(usdt.get("free", 0), 2),
            "usdt_total": round(usdt.get("total", 0), 2),
        },
    }


# ---------------------------------------------------------------------------
# Test without saving
# ---------------------------------------------------------------------------
@router.post("/test")
def test_exchange(keys: ExchangeKeys):
    if keys.exchange_name == "paper":
        return {
            "status": "success",
            "message": "Paper Trading connection successful",
            "balance": {"usdt_free": 0, "usdt_total": 0},
        }

    success, detail = test_connection(keys.api_key, keys.api_secret)
    if success:
        live_balance = get_live_balance(keys.api_key, keys.api_secret)
        usdt = live_balance.get("USDT", {})
        return {
            "status": "success",
            "message": "Connection test successful",
            "balance": {
                "usdt_free":  round(usdt.get("free", 0), 2),
                "usdt_total": round(usdt.get("total", 0), 2),
            },
        }
    else:
        raise HTTPException(status_code=400, detail=f"API connection failed: {detail}")


# ---------------------------------------------------------------------------
# Status — is an account connected?
# ---------------------------------------------------------------------------
@router.get("/status")
def exchange_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Returns connection status and live balance if connected."""
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user["id"]
    ).first()

    if not account:
        return {"connected": False, "testnet": settings.BYBIT_TESTNET, "balance": None}

    if account.exchange_name == "paper":
        from shared.db.models import Balance
        b = db.query(Balance).filter(Balance.account_id == account.id, Balance.asset == "USDT").first()
        usdt_free = b.free if b else 0.0
        usdt_total = (b.free + b.locked) if b else 0.0
        return {
            "connected": True,
            "testnet": account.is_testnet,
            "exchange": account.exchange_name,
            "balance": {
                "usdt_free": round(usdt_free, 2),
                "usdt_total": round(usdt_total, 2),
                "usd_value": round(usdt_total, 2),
            }
        }

    live_balance = get_live_balance(account.api_key, account.api_secret)
    usdt = live_balance.get("USDT", {})

    return {
        "connected": True,
        "testnet": account.is_testnet,
        "exchange": account.exchange_name,
        "balance": {
            "usdt_free":  round(usdt.get("free", 0), 2),
            "usdt_total": round(usdt.get("total", 0), 2),
            "usd_value":  round(usdt.get("usd_value", usdt.get("total", 0)), 2),
        }
    }

class FundRequest(BaseModel):
    amount: float

@router.post("/paper/fund")
def fund_paper_account(
    req: FundRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add or remove paper money from a paper trading account."""
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user["id"],
        ExchangeAccount.exchange_name == "paper"
    ).first()
    
    if not account:
        # Create paper account automatically
        account = ExchangeAccount(
            user_id=current_user["id"],
            exchange_name="paper",
            api_key="mock",
            api_secret="mock",
            is_testnet=True,
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        
    from shared.db.models import Balance
    b = db.query(Balance).filter(Balance.account_id == account.id, Balance.asset == "USDT").first()
    if not b:
        b = Balance(account_id=account.id, asset="USDT", free=req.amount, locked=0.0)
        db.add(b)
    else:
        b.free += req.amount
        
    db.commit()
    return {"status": "success", "message": f"Added ${req.amount} mock USDT."}


# ---------------------------------------------------------------------------
# Market scan — top pairs by opportunity
# ---------------------------------------------------------------------------
@router.get("/market/scan")
def market_scan(
    current_user: dict = Depends(get_current_user),
    top_n: int = 20,
):
    """Returns the top USDT pairs ranked by volume, momentum and volatility."""
    pairs = scan_market(top_n=top_n, min_volume_usdt=settings.MIN_24H_VOLUME_USDT)
    return {"status": "success", "data": pairs}

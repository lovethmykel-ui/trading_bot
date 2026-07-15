import time
import logging
import requests
from typing import Optional, List, Dict, Any, Tuple
from pybit.unified_trading import HTTP
from pybit import _helpers
from apps.api.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Clock sync: keeps local timestamps aligned with Bybit's server time
# ---------------------------------------------------------------------------
_time_offset = 0.0
_last_sync_time = 0.0

def sync_bybit_time():
    global _time_offset, _last_sync_time
    if time.time() - _last_sync_time < 300:
        return
    try:
        subdomain = "api-testnet" if settings.BYBIT_TESTNET else "api"
        url = f"https://{subdomain}.bybit.com/v5/market/time"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("retCode") == 0:
                server_time_ms = int(data.get("time", 0))
                if server_time_ms > 0:
                    local_time_ms = int(time.time() * 1000)
                    _time_offset = (server_time_ms - local_time_ms) / 1000.0
                    _last_sync_time = time.time()
                    logger.info(f"Bybit time synced. Offset: {_time_offset:.3f}s")
    except Exception as e:
        logger.warning(f"Bybit time sync failed: {e}")

def patched_generate_timestamp():
    sync_bybit_time()
    return int((time.time() + _time_offset) * 1000)

# Apply the clock patch to pybit
_helpers.generate_timestamp = patched_generate_timestamp


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------
def get_bybit_client(api_key: str = None, api_secret: str = None) -> HTTP:
    """Initializes an authenticated Bybit HTTP session."""
    return HTTP(
        testnet=settings.BYBIT_TESTNET,
        api_key=api_key,
        api_secret=api_secret,
        recv_window=15000,
    )

def get_public_client() -> HTTP:
    """Unauthenticated client for public market data."""
    return HTTP(testnet=settings.BYBIT_TESTNET)


# ---------------------------------------------------------------------------
# Connection test
# ---------------------------------------------------------------------------
def test_connection(api_key: str, api_secret: str) -> Tuple[bool, Any]:
    try:
        session = get_bybit_client(api_key, api_secret)
        response = session.get_wallet_balance(accountType="UNIFIED", coin="USDT")
        return True, response
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------
def get_live_balance(api_key: str, api_secret: str) -> Dict[str, Any]:
    """
    Returns the UNIFIED account balance from Bybit.
    Returns a dict like: {coin: {free, locked, total}}
    """
    try:
        session = get_bybit_client(api_key, api_secret)
        resp = session.get_wallet_balance(accountType="UNIFIED")
        import json
        with open("bybit_raw_balance.json", "w") as f:
            json.dump(resp, f, indent=2)
        print(">>> Wrote bybit_raw_balance.json")
        if resp.get("retCode") != 0:
            logger.error(f"Balance fetch error: {resp}")
            return {}

        result = {}
        for account in resp.get("result", {}).get("list", []):
            for coin_data in account.get("coin", []):
                coin = coin_data.get("coin", "")
                result[coin] = {
                    "free":   float(coin_data.get("availableToWithdraw", 0) or 0),
                    "locked": float(coin_data.get("locked", 0) or 0),
                    "total":  float(coin_data.get("walletBalance", 0) or 0),
                    "usd_value": float(coin_data.get("usdValue", 0) or 0),
                }
        return result
    except Exception as e:
        logger.error(f"get_live_balance error: {e}")
        return {}


# ---------------------------------------------------------------------------
# Positions
# ---------------------------------------------------------------------------
def get_live_positions(api_key: str, api_secret: str, symbol: str = None) -> List[Dict[str, Any]]:
    """Fetch all open positions (or positions for a specific symbol)."""
    try:
        session = get_bybit_client(api_key, api_secret)
        params = {"category": "linear", "settleCoin": "USDT"}
        if symbol:
            params["symbol"] = symbol
        resp = session.get_positions(**params)
        if resp.get("retCode") != 0:
            return []

        positions = []
        for pos in resp.get("result", {}).get("list", []):
            size = float(pos.get("size", 0) or 0)
            if size == 0:
                continue
            positions.append({
                "symbol":       pos.get("symbol"),
                "side":         pos.get("side"),     # Buy / Sell
                "size":         size,
                "entry_price":  float(pos.get("avgPrice", 0) or 0),
                "mark_price":   float(pos.get("markPrice", 0) or 0),
                "unrealized_pnl": float(pos.get("unrealisedPnl", 0) or 0),
                "leverage":     float(pos.get("leverage", 1) or 1),
                "liq_price":    float(pos.get("liqPrice", 0) or 0),
            })
        return positions
    except Exception as e:
        logger.error(f"get_live_positions error: {e}")
        return []


# ---------------------------------------------------------------------------
# Leverage
# ---------------------------------------------------------------------------
def set_leverage(api_key: str, api_secret: str, symbol: str, leverage: int = 5) -> bool:
    """Set leverage for a linear (USDT perpetual) contract."""
    try:
        session = get_bybit_client(api_key, api_secret)
        resp = session.set_leverage(
            category="linear",
            symbol=symbol,
            buyLeverage=str(leverage),
            sellLeverage=str(leverage),
        )
        return resp.get("retCode") == 0
    except Exception as e:
        logger.error(f"set_leverage error: {e}")
        return False


# ---------------------------------------------------------------------------
# Place live order
# ---------------------------------------------------------------------------
def place_live_order(
    api_key: str,
    api_secret: str,
    symbol: str,
    side: str,          # "Buy" or "Sell"
    qty: float,         # in base currency (e.g. BTC)
    order_type: str = "Market",
    stop_loss: float = None,
    take_profit: float = None,
) -> Dict[str, Any]:
    """
    Places a real order on Bybit (linear perpetual futures).
    Returns the Bybit order response dict.
    """
    try:
        session = get_bybit_client(api_key, api_secret)
        params: Dict[str, Any] = {
            "category":  "linear",
            "symbol":    symbol,
            "side":      side,
            "orderType": order_type,
            "qty":       str(qty),
            "timeInForce": "GTC" if order_type != "Market" else "IOC",
        }
        if stop_loss:
            params["stopLoss"] = str(round(stop_loss, 4))
        if take_profit:
            params["takeProfit"] = str(round(take_profit, 4))

        resp = session.place_order(**params)
        if resp.get("retCode") != 0:
            logger.error(f"place_live_order failed: {resp}")
            return {"error": resp.get("retMsg", "Unknown error"), "raw": resp}

        return {
            "order_id":  resp["result"].get("orderId"),
            "symbol":    symbol,
            "side":      side,
            "qty":       qty,
            "status":    "submitted",
        }
    except Exception as e:
        logger.error(f"place_live_order exception: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Get live price
# ---------------------------------------------------------------------------
def get_live_price(symbol: str) -> Optional[float]:
    """Fetch the latest mark price for a symbol."""
    try:
        client = get_public_client()
        resp = client.get_tickers(category="linear", symbol=symbol)
        if resp.get("retCode") == 0:
            items = resp.get("result", {}).get("list", [])
            if items:
                return float(items[0].get("markPrice", 0) or 0)
        return None
    except Exception as e:
        logger.error(f"get_live_price error for {symbol}: {e}")
        return None


# ---------------------------------------------------------------------------
# Get OHLCV candles
# ---------------------------------------------------------------------------
def get_candles(symbol: str, interval: str = "5", limit: int = 200) -> List[Dict[str, Any]]:
    """
    Fetch OHLCV candles from Bybit.
    interval: "1","3","5","15","30","60","120","240","D","W","M"
    Returns list of dicts sorted oldest→newest.
    """
    try:
        client = get_public_client()
        resp = client.get_kline(
            category="linear",
            symbol=symbol,
            interval=interval,
            limit=limit,
        )
        if resp.get("retCode") != 0:
            return []

        candles = []
        for row in reversed(resp.get("result", {}).get("list", [])):
            # row = [timestamp_ms, open, high, low, close, volume, turnover]
            candles.append({
                "timestamp": int(row[0]),
                "open":      float(row[1]),
                "high":      float(row[2]),
                "low":       float(row[3]),
                "close":     float(row[4]),
                "volume":    float(row[5]),
            })
        return candles
    except Exception as e:
        logger.error(f"get_candles error for {symbol}: {e}")
        return []


# ---------------------------------------------------------------------------
# Market scanner — find profitable pairs across the full USDT market
# ---------------------------------------------------------------------------
def scan_market(
    top_n: int = 20,
    min_volume_usdt: float = 10_000_000,
) -> List[Dict[str, Any]]:
    """
    Scans ALL linear USDT perpetual pairs on Bybit.
    Returns top_n pairs ranked by a composite score:
      - 24h volume (liquidity filter)
      - 24h price change % (momentum)
      - Volatility proxy (high-low range %)
    Only returns pairs above min_volume_usdt 24h turnover.
    """
    try:
        client = get_public_client()
        
        # Robust retry logic for network hiccups
        resp = {}
        for attempt in range(3):
            try:
                resp = client.get_tickers(category="linear")
                if resp.get("retCode") == 0:
                    break
                time.sleep(1)
            except Exception as e:
                if attempt == 2:
                    logger.error(f"scan_market API failed after 3 attempts: {e}")
                    return []
                time.sleep(1)

        if resp.get("retCode") != 0:
            logger.error(f"scan_market ticker fetch failed: {resp}")
            return []

        tickers = resp.get("result", {}).get("list", [])
        scored = []

        for t in tickers:
            symbol = t.get("symbol", "")
            status = t.get("status", "Trading")
            
            # Only USDT-margined perpetuals that are actively trading
            if not symbol.endswith("USDT") or status != "Trading":
                continue

            try:
                volume_24h    = float(t.get("turnover24h", 0) or 0)    # in USDT
                price_change  = float(t.get("price24hPcnt", 0) or 0)   # e.g. 0.023 = +2.3%
                high_24h      = float(t.get("highPrice24h", 0) or 1)
                low_24h       = float(t.get("lowPrice24h", 0) or 1)
                last_price    = float(t.get("lastPrice", 0) or 0)

                if volume_24h < min_volume_usdt or last_price <= 0:
                    continue

                # Volatility score: (high-low)/low — bigger range = more opportunity
                volatility    = (high_24h - low_24h) / low_24h if low_24h > 0 else 0

                # Composite score: weight volume + |momentum| + volatility
                # We want high-volume, high-momentum, high-volatility pairs
                score = (
                    (volume_24h / 1_000_000) * 0.4          # normalised volume weight
                    + abs(price_change) * 100 * 0.4          # momentum weight
                    + volatility * 100 * 0.2                 # volatility weight
                )

                scored.append({
                    "symbol":        symbol,
                    "last_price":    last_price,
                    "volume_24h":    volume_24h,
                    "price_change":  round(price_change * 100, 2),
                    "volatility":    round(volatility * 100, 2),
                    "score":         round(score, 2),
                })
            except (ValueError, TypeError):
                continue

        # Sort by composite score and return top N
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_n]

    except Exception as e:
        logger.error(f"scan_market error: {e}")
        return []


# ---------------------------------------------------------------------------
# Order history from Bybit
# ---------------------------------------------------------------------------
def get_order_history(api_key: str, api_secret: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent order history from Bybit."""
    try:
        session = get_bybit_client(api_key, api_secret)
        resp = session.get_order_history(category="linear", limit=limit)
        if resp.get("retCode") != 0:
            return []
        orders = []
        for o in resp.get("result", {}).get("list", []):
            orders.append({
                "order_id":   o.get("orderId"),
                "symbol":     o.get("symbol"),
                "side":       o.get("side"),
                "order_type": o.get("orderType"),
                "qty":        float(o.get("qty", 0) or 0),
                "price":      float(o.get("price", 0) or 0),
                "avg_price":  float(o.get("avgPrice", 0) or 0),
                "status":     o.get("orderStatus"),
                "created_at": o.get("createdTime"),
            })
        return orders
    except Exception as e:
        logger.error(f"get_order_history error: {e}")
        return []

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from apps.api.core.security import get_current_user

router = APIRouter()

from apps.api.core.bybit import get_bybit_client

@router.get("/data", response_model=Dict[str, Any])
async def get_market_data(
    symbol: str = Query(..., description="The trading pair symbol (e.g., BTCUSDT)"),
    interval: str = Query("15", description="Kline interval (e.g., 1, 5, 15, 60, D)"),
    limit: int = Query(200, description="Number of candles to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get historical kline/candle data for a specific symbol directly from Bybit API.
    """
    try:
        # Initialize an unauthenticated Bybit client for public market data
        client = get_bybit_client()

        # Fetch klines (OHLCV)
        # Bybit API structure: category='linear' for futures, 'spot' for spot
        response = client.get_kline(
            category="linear",
            symbol=symbol,
            interval=interval,
            limit=limit
        )

        # Bybit returns a list of lists: [startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover]
        formatted_data = []
        if response and "result" in response and "list" in response["result"]:
            kline_list = response["result"]["list"]
            # Bybit returns newest first, so we reverse it for chronological order
            for kline in reversed(kline_list):
                formatted_data.append({
                    "timestamp": int(kline[0]),
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5])
                })

        return {
            "symbol": symbol,
            "interval": interval,
            "data": formatted_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")

@router.get("/orderbook", response_model=Dict[str, Any])
async def get_orderbook(
    symbol: str = Query("BTCUSDT"),
    limit: int = Query(50, description="Depth of the orderbook (1, 50, 200)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get live orderbook depth/liquidity from Bybit.
    Used by the frontend to render the Order Flow heatmaps.
    """
    try:
        client = get_bybit_client()
        response = client.get_orderbook(category="linear", symbol=symbol, limit=limit)

        bids = []
        asks = []

        if response and "result" in response:
            res = response["result"]
            # Bybit returns bids/asks as ["price", "size"] strings
            bids = [{"price": float(b[0]), "size": float(b[1])} for b in res.get("b", [])]
            asks = [{"price": float(a[0]), "size": float(a[1])} for a in res.get("a", [])]

        return {
            "status": "success",
            "symbol": symbol,
            "bids": bids,
            "asks": asks,
            "timestamp": response.get("time") if response else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orderbook: {str(e)}")

@router.get("/indicators", response_model=Dict[str, Any])
async def get_market_indicators(
    symbol: str = Query(..., description="The trading pair symbol (e.g., BTCUSDT)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Trigger the Indicator Engine (Sprint 2) to calculate indicators for a symbol.
    """
    from services.indicator_engine.tasks import get_latest_signals

    # In a real app, we would query the DB or Bybit for the last X candles here.
    # For now, we mock the OHLCV payload to pass to the engine.
    mock_ohlcv = [
        {"open": 64000.0, "high": 64500.0, "low": 63800.0, "close": 64200.0, "volume": 100.0}
        for _ in range(100) # Give it 100 candles so 50-EMA and Ichimoku can calculate
    ]

    # Call the Celery task (or just the imported function directly for now since Celery worker setup failed in tests)
    try:
        # For demo purposes, we will call it synchronously here if Celery isn't running
        # In production this should be async: get_latest_signals.delay(mock_ohlcv)
        signals = get_latest_signals(mock_ohlcv)
        return {
            "symbol": symbol,
            "indicators": signals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indicator calculation failed: {str(e)}")

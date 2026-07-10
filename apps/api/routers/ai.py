from fastapi import APIRouter, Depends, Query
from typing import Dict, Any

from apps.api.core.security import get_current_user
from ai.ensemble.engine import ConsensusEngine

router = APIRouter()
engine = ConsensusEngine()

from apps.api.core.bybit import get_bybit_client

from ai.backtesting.engine import BacktestEngine

@router.post("/backtest", response_model=Dict[str, Any])
def run_backtest(
    symbol: str = Query("BTCUSDT"),
    current_user: dict = Depends(get_current_user)
):
    """
    Triggers the Historical Replay Engine to evaluate the AI Ensemble over past data.
    """
    try:
        # Fetch a larger chunk of historical data for backtesting (e.g. 50 days)
        client = get_bybit_client()
        kline_res = client.get_kline(category="linear", symbol=symbol, interval="D", limit=50)

        historical_data = []
        if kline_res and "result" in kline_res and "list" in kline_res["result"]:
            klist = kline_res["result"]["list"]
            for k in reversed(klist): # chronological
                historical_data.append({
                    "timestamp": k[0],
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5])
                })

        # Run Backtest
        bt_engine = BacktestEngine(initial_capital=100000.0, risk_per_trade=1.0)
        results = bt_engine.run_backtest(symbol=symbol, historical_data=historical_data)

        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/consensus", response_model=Dict[str, Any])
def get_ai_consensus(
    symbol: str = Query("BTCUSDT"),
    current_user: dict = Depends(get_current_user)
):
    """
    Triggers the Intelligence Layer ensemble of specialized AI agents.
    Now injects live market data from Bybit to feed the LLM prompts.
    """
    try:
        # 1. Fetch live market context
        client = get_bybit_client()
        kline_res = client.get_kline(category="linear", symbol=symbol, interval="D", limit=10)

        # Format the context payload to inject into the LLM prompts
        market_data = {
            "symbol": symbol,
            "recent_daily_klines": kline_res.get("result", {}).get("list", []),
            "current_price": None,
            "news_headlines": [
                "Fed hints at potential rate cuts in Q3.",
                "Bitcoin ETF inflows reach new all-time high."
            ], # Mocked external data API for Sentiment/Macro agents
            "social_fear_greed_index": 78 # Mocked
        }

        if market_data["recent_daily_klines"]:
            market_data["current_price"] = float(market_data["recent_daily_klines"][0][4]) # Close price of latest candle

        # 2. Run the Multi-Agent LLM Ensemble
        consensus_result = engine.run_consensus(market_data)

        return {
            "status": "success",
            "data": consensus_result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

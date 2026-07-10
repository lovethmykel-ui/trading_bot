from fastapi import APIRouter, Depends, Query
from typing import Dict, Any

from apps.api.core.security import get_current_user
from ai.ensemble.engine import ConsensusEngine

router = APIRouter()
engine = ConsensusEngine()

@router.get("/consensus", response_model=Dict[str, Any])
def get_ai_consensus(
    symbol: str = Query("BTCUSDT"),
    current_user: dict = Depends(get_current_user)
):
    """
    Triggers the Intelligence Layer ensemble of specialized AI agents.
    In a live environment, this would fetch current market data to pass to the agents.
    """

    # Mocking market data for the agents to analyze (Sprint 4 MVP)
    market_data = {
        "symbol": symbol,
        "price": 64250.0,
        "ema_50": 64000.0, # Bullish trend mock
    }

    consensus_result = engine.run_consensus(market_data)

    return {
        "status": "success",
        "data": consensus_result
    }

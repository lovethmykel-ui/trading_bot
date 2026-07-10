import os
from celery import Celery
import pandas as pd
from typing import Dict, Any, List

from .engine import IndicatorEngine

# Read Redis URL from environment or fallback to default
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    "indicator_engine",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="indicator_engine.calculate_indicators")
def calculate_indicators(ohlcv_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Celery task to calculate technical indicators on a payload of OHLCV data.

    Args:
        ohlcv_data: List of dictionaries containing 'open', 'high', 'low', 'close', 'volume'

    Returns:
        List of dictionaries with the original OHLCV data plus calculated indicators.
    """
    try:
        # Convert JSON-serializable list of dicts to pandas DataFrame
        df = pd.DataFrame(ohlcv_data)

        # Run calculations
        result_df = IndicatorEngine.calculate_all(df)

        # Replace NaNs with None for JSON serialization compatibility
        result_df = result_df.where(pd.notnull(result_df), None)

        # Convert back to list of dicts
        return result_df.to_dict(orient="records")

    except Exception as e:
        # In a real system, we'd log this properly
        return {"error": str(e)}

@celery_app.task(name="indicator_engine.get_latest_signals")
def get_latest_signals(ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates indicators and returns only the very last row's values.
    Used for fast signal generation.
    """
    try:
        df = pd.DataFrame(ohlcv_data)
        return IndicatorEngine.get_latest_signals(df)
    except Exception as e:
        return {"error": str(e)}

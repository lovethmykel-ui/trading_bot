import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Dict, Any, List

class IndicatorEngine:
    """
    Core calculation engine for technical indicators.
    Takes an OHLCV DataFrame and computes an institutional-grade set of indicators.
    """

    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> bool:
        """Ensure the dataframe has the required OHLCV columns."""
        required_cols = {'open', 'high', 'low', 'close', 'volume'}
        # Lowercase all columns for consistency
        df.columns = df.columns.str.lower()
        return required_cols.issubset(df.columns)

    @classmethod
    def calculate_all(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates all Sprint 2 requested indicators simultaneously.
        • EMA
        • RSI
        • MACD
        • Bollinger Bands
        • VWAP
        • ATR
        • ADX
        • SuperTrend
        • OBV
        • Ichimoku
        """
        if not cls.validate_dataframe(df):
            raise ValueError("DataFrame must contain 'open', 'high', 'low', 'close', and 'volume' columns.")

        # Make a copy to avoid SettingWithCopyWarnings
        df = df.copy()

        # 1. EMA (Exponential Moving Average) - Standard 20 and 50 periods
        df['EMA_20'] = ta.ema(df['close'], length=20)
        df['EMA_50'] = ta.ema(df['close'], length=50)

        # 2. RSI (Relative Strength Index) - Standard 14 periods
        df['RSI_14'] = ta.rsi(df['close'], length=14)

        # 3. MACD (Moving Average Convergence Divergence) - Standard 12, 26, 9
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd is not None:
            df = pd.concat([df, macd], axis=1)

        # 4. Bollinger Bands - Standard 20 period, 2 std dev
        bbands = ta.bbands(df['close'], length=20, std=2)
        if bbands is not None:
            df = pd.concat([df, bbands], axis=1)

        # 5. VWAP (Volume Weighted Average Price)
        # Note: pandas_ta requires a DateTimeIndex or an explicit 'datetime' column for anchored VWAP
        # Fallback to standard VWAP calculation if anchoring fails
        try:
            vwap = ta.vwap(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'])
            if vwap is not None:
                df['VWAP'] = vwap
        except Exception:
            # Fallback simple VWAP if index isn't properly formatted
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            df['VWAP'] = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()

        # 6. ATR (Average True Range) - Standard 14 periods
        df['ATR_14'] = ta.atr(high=df['high'], low=df['low'], close=df['close'], length=14)

        # 7. ADX (Average Directional Index) - Standard 14 periods
        adx = ta.adx(high=df['high'], low=df['low'], close=df['close'], length=14)
        if adx is not None:
            df = pd.concat([df, adx], axis=1)

        # 8. SuperTrend - Standard 7 period, 3.0 multiplier
        supertrend = ta.supertrend(high=df['high'], low=df['low'], close=df['close'], length=7, multiplier=3.0)
        if supertrend is not None:
            df = pd.concat([df, supertrend], axis=1)

        # 9. OBV (On-Balance Volume)
        df['OBV'] = ta.obv(close=df['close'], volume=df['volume'])

        # 10. Ichimoku Cloud - Standard 9, 26, 52 settings
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ichimoku, _ = ta.ichimoku(high=df['high'], low=df['low'], close=df['close'], tenkan=9, kijun=26, senkou=52)
        if ichimoku is not None:
            df = pd.concat([df, ichimoku], axis=1)

        return df

    @classmethod
    def get_latest_signals(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Returns the most recent calculated indicator values as a dictionary.
        Useful for passing signals to the consensus/intelligence engine.
        """
        # Ensure calculations are performed
        if 'RSI_14' not in df.columns:
            df = cls.calculate_all(df)

        # Get the last row, dropping any NA values from that row to provide a clean dictionary
        latest = df.iloc[-1].to_dict()

        # Convert any numpy NaN values to Python None for JSON serialization compatibility
        clean_latest = {k: (None if pd.isna(v) else v) for k, v in latest.items()}

        return clean_latest

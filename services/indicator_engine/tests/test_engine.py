import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to path for module resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.indicator_engine.engine import IndicatorEngine

class TestIndicatorEngine(unittest.TestCase):

    def setUp(self):
        """Create mock OHLCV data for testing."""
        # Need enough rows to calculate 52-period Ichimoku and 50-period EMA
        periods = 100

        # Create a trending price action
        base_price = 50000
        trend = np.linspace(0, 1000, periods)
        noise = np.random.normal(0, 50, periods)
        closes = base_price + trend + noise

        self.df = pd.DataFrame({
            'open': closes - np.random.uniform(10, 50, periods),
            'high': closes + np.random.uniform(10, 100, periods),
            'low': closes - np.random.uniform(50, 150, periods),
            'close': closes,
            'volume': np.random.uniform(1, 10, periods)
        })
        # Add index for VWAP
        self.df.index = pd.date_range(start='2023-01-01', periods=periods, freq='D')

    def test_validation(self):
        """Test DataFrame schema validation."""
        valid = IndicatorEngine.validate_dataframe(self.df)
        self.assertTrue(valid)

        invalid_df = self.df.drop(columns=['volume'])
        valid = IndicatorEngine.validate_dataframe(invalid_df)
        self.assertFalse(valid)

    def test_calculate_all(self):
        """Test that all indicators are calculated and added to the DataFrame."""
        result_df = IndicatorEngine.calculate_all(self.df)

        # Check that original columns exist
        for col in ['open', 'high', 'low', 'close', 'volume']:
            self.assertIn(col, result_df.columns)

        # Check that expected indicator columns exist
        expected_indicators = [
            'EMA_20', 'EMA_50', 'RSI_14',
            'MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9', # MACD output
            'BBL_20_2.0_2.0', 'BBM_20_2.0_2.0', 'BBU_20_2.0_2.0',         # Bollinger Bands output
            'VWAP', 'ATR_14',
            'ADX_14',                                         # ADX output
            'SUPERT_7_3.0',                                   # SuperTrend output
            'OBV',
            'ISA_9', 'ISB_26', 'ITS_9', 'IKS_26', 'ICS_26'    # Ichimoku output
        ]

        for indicator in expected_indicators:
            self.assertIn(indicator, result_df.columns, f"Missing indicator column: {indicator}")

    def test_get_latest_signals(self):
        """Test that the latest signals dictionary is properly formed."""
        signals = IndicatorEngine.get_latest_signals(self.df)

        self.assertIsInstance(signals, dict)
        self.assertIn('close', signals)
        self.assertIn('EMA_20', signals)
        self.assertIn('RSI_14', signals)

        # The latest values should not be NaN since we have 100 rows
        self.assertIsNotNone(signals['EMA_50'])
        self.assertIsNotNone(signals['RSI_14'])

if __name__ == '__main__':
    unittest.main()

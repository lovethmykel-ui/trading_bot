import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.risk_engine.calculator import RiskManager

class TestRiskManager(unittest.TestCase):
    def test_calculate_position_size(self):
        # 100k balance, 1% risk ($1000). Entry 50k, Stop 49k (Risk per unit = $1000)
        # Expected size: 1.0 BTC
        res = RiskManager.calculate_position_size(100000, 1.0, 50000, 49000)
        self.assertEqual(res['size'], 1.0)
        self.assertEqual(res['risk_amount'], 1000.0)
        self.assertEqual(res['total_exposure'], 50000.0)

    def test_calculate_kelly_fraction(self):
        # 50% win rate, win $2, lose $1. R = 2
        # Kelly = 0.5 - (0.5 / 2) = 0.5 - 0.25 = 0.25
        # Half Kelly = 0.125 = 12.5%
        res = RiskManager.calculate_kelly_fraction(0.5, 2.0, 1.0, half_kelly=True)
        self.assertEqual(res['full_kelly'], 0.25)
        self.assertEqual(res['recommended_risk_pct'], 12.5)

    def test_trailing_stop_long(self):
        # Long from 100. Highest price 110. Trailing distance 10%.
        # Expected stop = 110 - 11 = 99
        stop = RiskManager.calculate_trailing_stop('LONG', 105, 110, 100, 10.0)
        self.assertEqual(stop, 99.0)

if __name__ == '__main__':
    unittest.main()
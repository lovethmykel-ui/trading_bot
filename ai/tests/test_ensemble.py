import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ensemble.engine import ConsensusEngine
from models.schema import AgentSignal

class TestIntelligenceLayer(unittest.TestCase):
    def test_consensus_engine(self):
        engine = ConsensusEngine()

        # Mock market data
        data = {"price": 100, "ema_50": 90}

        # Run consensus
        result = engine.run_consensus(data)

        # Validate output schema structure
        self.assertIn("final_decision", result)
        self.assertIn("overall_confidence", result)
        self.assertIn("is_trade_recommended", result)
        self.assertIn("agent_breakdown", result)

        # Validate logic (we expect a boolean for trade recommended)
        self.assertIsInstance(result["is_trade_recommended"], bool)

        # Validate agent breakdown contains all 7 specialized agents
        self.assertEqual(len(result["agent_breakdown"]), 7)

        for agent_data in result["agent_breakdown"]:
            self.assertIn("agent", agent_data)
            self.assertIn("signal", agent_data)
            self.assertIn(agent_data["signal"], ["LONG", "SHORT", "NEUTRAL"])
            self.assertIn("confidence", agent_data)

if __name__ == '__main__':
    unittest.main()
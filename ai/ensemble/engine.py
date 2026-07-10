from typing import Any, Dict, List
from ai.models.schema import AgentSignal
from ai.ensemble.agents import get_all_agents

class ConsensusEngine:
    """
    Ingests signals from all specialized agents and arrives at a unified trading decision.
    """
    def __init__(self):
        self.agents = get_all_agents()

    def run_consensus(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs all agents concurrently (simulated) and aggregates their opinions.
        """
        signals: List[AgentSignal] = []

        # 1. Collect signals from all agents
        for agent in self.agents:
            signal = agent.analyze(market_data)
            signals.append(signal)

        # 2. Calculate aggregations
        long_weight = 0
        short_weight = 0
        neutral_weight = 0

        for sig in signals:
            if sig.signal == "LONG":
                long_weight += sig.confidence
            elif sig.signal == "SHORT":
                short_weight += sig.confidence
            else:
                neutral_weight += sig.confidence

        total_weight = long_weight + short_weight + neutral_weight

        # 3. Determine Final Bias
        if total_weight == 0:
            final_decision = "NEUTRAL"
            overall_confidence = 0
        else:
            if long_weight > short_weight and long_weight > neutral_weight:
                final_decision = "LONG"
                overall_confidence = int((long_weight / total_weight) * 100)
            elif short_weight > long_weight and short_weight > neutral_weight:
                final_decision = "SHORT"
                overall_confidence = int((short_weight / total_weight) * 100)
            else:
                final_decision = "NEUTRAL"
                overall_confidence = int((neutral_weight / total_weight) * 100)

        # Ensure we only trade on high conviction (arbitrary threshold of 60 for MVP)
        trade_ready = overall_confidence >= 60 and final_decision != "NEUTRAL"

        return {
            "final_decision": final_decision,
            "overall_confidence": overall_confidence,
            "is_trade_recommended": trade_ready,
            "agent_breakdown": [sig.model_dump() for sig in signals]
        }

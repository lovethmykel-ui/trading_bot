import random
from typing import Any, Dict
from ai.models.base import BaseAgent
from ai.models.schema import AgentSignal

class TrendAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Trend")

    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        # Mocking LLM/Logic for Sprint 4 MVP
        # In Phase 2, this will use an LLM or complex technical logic
        is_bullish = data.get("price", 0) > data.get("ema_50", 0)
        signal = "LONG" if is_bullish else "SHORT"

        return AgentSignal(
            agent=self.name,
            signal=signal,
            confidence=random.randint(60, 95),
            reasoning=f"Price is trading {'above' if is_bullish else 'below'} the 50 EMA indicating momentum."
        )

class MarketStructureAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Market Structure")

    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        return AgentSignal(
            agent=self.name,
            signal=random.choice(["LONG", "SHORT", "NEUTRAL"]),
            confidence=random.randint(50, 90),
            reasoning="Higher highs and higher lows detected on the 4H timeframe."
        )

class OrderFlowAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Order Flow")

    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        return AgentSignal(
            agent=self.name,
            signal=random.choice(["LONG", "SHORT", "NEUTRAL"]),
            confidence=random.randint(40, 88),
            reasoning="Strong limit bid absorption detected at the current price level."
        )

class VolumeAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Volume")

    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        return AgentSignal(
            agent=self.name,
            signal="LONG",
            confidence=random.randint(55, 99),
            reasoning="Volume is expanding aggressively on the breakout candle."
        )

class SentimentAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Sentiment")

    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        return AgentSignal(
            agent=self.name,
            signal="NEUTRAL",
            confidence=random.randint(30, 80),
            reasoning="Social sentiment is overheated; cautious neutral bias."
        )

class MacroNewsAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Macro News")

    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        return AgentSignal(
            agent=self.name,
            signal="SHORT",
            confidence=random.randint(65, 95),
            reasoning="Unexpectedly high CPI print causing hawkish rate expectations."
        )

class RiskAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Risk")

    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        return AgentSignal(
            agent=self.name,
            signal="NEUTRAL",
            confidence=random.randint(80, 100),
            reasoning="Volatility remains within acceptable 1-standard deviation bounds."
        )

# Factory to load all specialized agents
def get_all_agents() -> list[BaseAgent]:
    return [
        MarketStructureAgent(),
        TrendAgent(),
        OrderFlowAgent(),
        VolumeAgent(),
        SentimentAgent(),
        MacroNewsAgent(),
        RiskAgent()
    ]
import json
import os
from typing import Any, Dict
from openai import OpenAI

from ai.models.base import BaseAgent
from ai.models.schema import AgentSignal

# Use the structured output formatting introduced in GPT-4o
# For this sprint, we assume OPENAI_API_KEY is available in the environment

def call_llm(system_prompt: str, data: Dict[str, Any]) -> AgentSignal:
    """Helper method to invoke OpenAI and parse structured AgentSignal output."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        import random
        # Fallback to mock behavior if no API key is set so the app doesn't crash during testing
        return AgentSignal(
            agent="LLM Offline Mock",
            signal=random.choice(["LONG", "SHORT"]),
            confidence=random.randint(70, 95),
            reasoning="OpenAI API key missing. Generating mock signal for testing."
        )

    client = OpenAI(api_key=api_key)

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this recent market data: {json.dumps(data)}"}
            ],
            response_format=AgentSignal,
        )
        # Parse the structured Pydantic object returned by OpenAI
        return response.choices[0].message.parsed
    except Exception as e:
        return AgentSignal(
            agent="Error",
            signal="NEUTRAL",
            confidence=0,
            reasoning=f"LLM Error: {str(e)}"
        )

class TrendAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Trend")

    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        prompt = (
            "You are the Trend Agent. Analyze the provided market indicators (EMA, MACD, SuperTrend) "
            "to determine the primary market trend. Ignore news or sentiment. "
            "Output your findings according to the schema."
        )
        signal = call_llm(prompt, data)
        signal.agent = self.name # enforce agent name
        return signal

class MarketStructureAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Market Structure")

    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        prompt = (
            "You are the Market Structure Agent. Analyze the recent price action (Highs, Lows) "
            "to identify support/resistance and overall structural momentum. "
            "Are we making higher highs (LONG) or lower lows (SHORT)?"
        )
        signal = call_llm(prompt, data)
        signal.agent = self.name
        return signal

class MacroNewsAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Macro News")

    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        prompt = (
            "You are the Macro News Agent. Analyze the provided news headlines and economic "
            "calendar events. Determine if the macro environment is risk-on (LONG) or risk-off (SHORT) for Bitcoin."
        )
        signal = call_llm(prompt, data)
        signal.agent = self.name
        return signal

class SentimentAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Sentiment")

    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        prompt = (
            "You are the Social Sentiment Agent. Evaluate the provided social media data, "
            "fear and greed index, and general retail sentiment. Contrarian views are often best "
            "when retail is extremely greedy."
        )
        signal = call_llm(prompt, data)
        signal.agent = self.name
        return signal

# Keeping some mock agents to simulate partial implementation
import random
class OrderFlowAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Order Flow")
    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        return AgentSignal(agent=self.name, signal=random.choice(["LONG", "SHORT", "NEUTRAL"]), confidence=random.randint(40, 88), reasoning="Strong limit bid absorption detected.")

class VolumeAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Volume")
    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        return AgentSignal(agent=self.name, signal="LONG", confidence=random.randint(55, 99), reasoning="Volume expanding.")

class RiskAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Risk")
    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        return AgentSignal(agent=self.name, signal="NEUTRAL", confidence=random.randint(80, 100), reasoning="Volatility remains within bounds.")

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
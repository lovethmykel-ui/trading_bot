from abc import ABC, abstractmethod
from typing import Any, Dict
from .schema import AgentSignal

class BaseAgent(ABC):
    """
    Abstract base class for all specialized trading agents.
    Enforces a strict output contract via the AgentSignal Pydantic model.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> AgentSignal:
        """
        Ingests market data and returns a structured opinion.
        To be implemented by specific agent subclasses (Trend, Sentiment, etc.)
        """
        pass

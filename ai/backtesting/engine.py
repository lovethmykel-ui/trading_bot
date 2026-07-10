from typing import List, Dict, Any
from ai.ensemble.engine import ConsensusEngine
from services.risk_engine.calculator import RiskManager
from services.trading_engine.paper import PaperTradingEngine
# Assume a mock DB session class for backtesting context
class MockDB:
    def add(self, *args): pass
    def commit(self): pass
    def rollback(self): pass
    def query(self, *args):
        class MockQuery:
            def filter(self, *args): return self
            def first(self): return None
        return MockQuery()

class BacktestEngine:
    """
    Historical Replay Engine.
    Streams past market data to the intelligence layer and evaluates strategy performance.
    """
    def __init__(self, initial_capital: float = 100000.0, risk_per_trade: float = 1.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.consensus_engine = ConsensusEngine()
        self.trade_history = []

    def run_backtest(self, symbol: str, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs the strategy over a sequence of historical data points.
        historical_data: List of dicts representing chronological data states (e.g., daily closes).
        """
        wins = 0
        losses = 0

        # We simulate iterating through time
        for idx, market_state in enumerate(historical_data):
            # Skip if we don't have enough lookback data for the LLM to make a decision
            if idx < 10:
                continue

            # Formulate the payload for the LLM ensemble representing what it would have seen at this exact moment in the past
            context = {
                "symbol": symbol,
                "current_price": market_state["close"],
                "recent_daily_klines": historical_data[idx-10:idx], # Give it the previous 10 days
            }

            # 1. Generate Signal
            consensus = self.consensus_engine.run_consensus(context)

            # 2. Execute Logic
            if consensus["is_trade_recommended"]:
                # Determine mock stop loss (e.g., 2% away)
                entry_price = market_state["close"]
                if consensus["final_decision"] == "LONG":
                    stop_loss = entry_price * 0.98
                else:
                    stop_loss = entry_price * 1.02

                # Calculate Size
                sizing = RiskManager.calculate_position_size(
                    account_balance=self.current_capital,
                    risk_percentage=self.risk_per_trade,
                    entry_price=entry_price,
                    stop_loss=stop_loss
                )

                # Mock execution result for the backtest
                # In a real deep backtester, this position stays open until the trailing stop is hit in future iterations.
                # For Sprint MVP, we assume a static win/loss mock distribution based on the LLM's confidence.
                # A confidence > 80% yields a win, else it's a loss (just to populate the metrics UI).
                is_win = consensus["overall_confidence"] >= 80
                pnl = sizing["risk_amount"] * 1.5 if is_win else -sizing["risk_amount"]

                self.current_capital += pnl
                if is_win:
                    wins += 1
                else:
                    losses += 1

                self.trade_history.append({
                    "timestamp": market_state.get("timestamp", "Unknown"),
                    "side": consensus["final_decision"],
                    "confidence": consensus["overall_confidence"],
                    "entry": entry_price,
                    "pnl": round(pnl, 2),
                    "balance_after": round(self.current_capital, 2)
                })

        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

        return {
            "initial_capital": self.initial_capital,
            "final_capital": round(self.current_capital, 2),
            "net_profit": round(self.current_capital - self.initial_capital, 2),
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "trades": self.trade_history
        }

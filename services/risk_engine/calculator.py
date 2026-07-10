from typing import Dict, Any, Optional

class RiskManager:
    """
    Core risk management logic for institutional trading.
    Handles position sizing, Kelly Formula calculations, and trailing stops.
    """

    @staticmethod
    def calculate_position_size(
        account_balance: float,
        risk_percentage: float,
        entry_price: float,
        stop_loss: float
    ) -> Dict[str, Any]:
        """
        Calculate the exact number of units to buy/sell based on total account risk.

        Formula:
        Risk Amount = Account Balance * (Risk Percentage / 100)
        Risk Per Share = |Entry - Stop Loss|
        Position Size = Risk Amount / Risk Per Share
        """
        if account_balance <= 0 or risk_percentage <= 0:
            return {"size": 0.0, "risk_amount": 0.0, "error": "Invalid balance or risk percentage"}

        if entry_price == stop_loss:
            return {"size": 0.0, "risk_amount": 0.0, "error": "Entry and Stop Loss cannot be equal"}

        risk_amount = account_balance * (risk_percentage / 100.0)
        risk_per_unit = abs(entry_price - stop_loss)

        position_size = risk_amount / risk_per_unit
        total_exposure = position_size * entry_price

        return {
            "size": round(position_size, 6),
            "risk_amount": round(risk_amount, 2),
            "risk_per_unit": round(risk_per_unit, 4),
            "total_exposure": round(total_exposure, 2),
            "leverage_required": round(total_exposure / account_balance, 2)
        }

    @staticmethod
    def calculate_kelly_fraction(
        win_rate: float,
        average_win: float,
        average_loss: float,
        half_kelly: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate the optimal fraction of the bankroll to risk using the Kelly Criterion.

        Formula:
        f* = W - ((1 - W) / R)
        where:
        W = Win Probability (Win Rate)
        R = Win/Loss Ratio (Average Win / Average Loss)
        """
        if win_rate < 0 or win_rate > 1:
            return {"kelly_fraction": 0.0, "error": "Win rate must be between 0 and 1"}

        if average_loss <= 0:
            return {"kelly_fraction": 0.0, "error": "Average loss must be strictly positive"}

        if average_win < 0:
            return {"kelly_fraction": 0.0, "error": "Average win must be positive"}

        # Win/Loss Ratio
        R = average_win / average_loss

        # Kelly Fraction
        kelly = win_rate - ((1 - win_rate) / R)

        # For risk management, institutional traders rarely use full Kelly due to volatility.
        # Half-Kelly is standard practice.
        recommended_fraction = (kelly / 2.0) if half_kelly else kelly

        # Clamp to 0 (don't trade if edge is negative)
        recommended_fraction = max(0.0, recommended_fraction)

        return {
            "full_kelly": round(kelly, 4),
            "recommended_risk_pct": round(recommended_fraction * 100, 2),
            "win_loss_ratio": round(R, 2)
        }

    @staticmethod
    def calculate_trailing_stop(
        side: str,
        current_price: float,
        highest_price_since_entry: float,
        lowest_price_since_entry: float,
        trailing_percentage: float
    ) -> float:
        """
        Calculates the new trailing stop price.

        Args:
            side: 'LONG' or 'SHORT'
            current_price: The current market price.
            highest_price_since_entry: The peak price reached while the long position was open.
            lowest_price_since_entry: The trough price reached while the short position was open.
            trailing_percentage: The percentage distance to trail (e.g., 2.5 for 2.5%).

        Returns:
            The calculated stop price.
        """
        trail_factor = trailing_percentage / 100.0

        if side.upper() == 'LONG':
            # Stop trails up below the highest price achieved
            stop_distance = highest_price_since_entry * trail_factor
            return highest_price_since_entry - stop_distance

        elif side.upper() == 'SHORT':
            # Stop trails down above the lowest price achieved
            stop_distance = lowest_price_since_entry * trail_factor
            return lowest_price_since_entry + stop_distance

        return 0.0

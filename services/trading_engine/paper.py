import logging
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, Optional

from shared.db.models import Balance, Position, Order, Trade, ExchangeAccount

logger = logging.getLogger(__name__)

class PaperTradingEngine:
    """
    Simulated trading environment for manual and algorithmic execution.
    Executes orders against live market data without risking real capital.
    """

    @staticmethod
    def execute_market_order(
        db: Session,
        account_id: int,
        symbol: str,
        side: str,
        size: float,
        current_market_price: float
    ) -> Dict[str, Any]:
        """
        Executes a simulated market order.
        1. Records the order.
        2. Records the trade.
        3. Updates balances (deducts quote currency, adds base currency).
        4. Updates or opens a position.
        """
        side = side.upper()
        if side not in ['LONG', 'SHORT', 'BUY', 'SELL']:
            return {"error": "Invalid side"}

        # Map BUY/SELL to LONG/SHORT for position tracking
        position_side = 'LONG' if side in ['BUY', 'LONG'] else 'SHORT'

        # 1. Create the Order Record
        order = Order(
            account_id=account_id,
            symbol=symbol,
            order_type='MARKET',
            side=side,
            price=current_market_price,
            amount=size,
            status='FILLED'
        )
        db.add(order)

        # 2. Create the Trade Record (Assume 0.05% taker fee for simulation)
        fee_rate = 0.0005
        trade_value = size * current_market_price
        fee = trade_value * fee_rate

        trade = Trade(
            account_id=account_id,
            symbol=symbol,
            side=side,
            price=current_market_price,
            amount=size,
            fee=fee
        )
        db.add(trade)

        # 3. Update Position
        position = db.query(Position).filter(
            Position.account_id == account_id,
            Position.symbol == symbol
        ).first()

        if position:
            if position.side == position_side:
                # Add to existing position (Average down/up)
                total_size = position.size + size
                new_entry = ((position.size * position.entry_price) + (size * current_market_price)) / total_size
                position.size = total_size
                position.entry_price = new_entry
            else:
                # Reduce or flip position
                if size < position.size:
                    # Partial close
                    position.size -= size
                    # Realize PnL would be calculated here
                elif size == position.size:
                    # Full close
                    db.delete(position)
                else:
                    # Flip position
                    position.side = position_side
                    position.size = size - position.size
                    position.entry_price = current_market_price
        else:
            # Open new position
            position = Position(
                account_id=account_id,
                symbol=symbol,
                side=position_side,
                size=size,
                entry_price=current_market_price
            )
            db.add(position)

        # 4. Update Balances (Simplified for MVP: Assuming USD/USDT quote currency)
        quote_currency = "USDT" # In reality, parse from symbol (e.g. BTCUSDT -> USDT)
        balance = db.query(Balance).filter(
            Balance.account_id == account_id,
            Balance.asset == quote_currency
        ).first()

        if not balance:
            # Seed paper trading account if it doesn't exist
            balance = Balance(account_id=account_id, asset=quote_currency, free=100000.0)
            db.add(balance)
            db.flush() # get ID

        # Deduct margin/cost and fees from free balance
        # For a simple spot paper trader, we deduct the whole value. For futures, it's just margin.
        # Assuming futures/margin simulation here where we deduct realized fees.
        balance.free -= fee

        try:
            db.commit()
            return {
                "status": "success",
                "order_id": order.id,
                "executed_price": current_market_price,
                "size": size,
                "fee": fee
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to execute paper trade: {str(e)}")
            return {"error": "Database error during execution"}

    @staticmethod
    def calculate_unrealized_pnl(position: Position, current_market_price: float) -> float:
        """Calculates current unrealized PnL for an open position."""
        if position.side == 'LONG':
            return (current_market_price - position.entry_price) * position.size
        else:
            return (position.entry_price - current_market_price) * position.size
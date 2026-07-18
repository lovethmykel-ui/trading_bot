import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from shared.db.models import Balance, Position, Order, Trade, ExchangeAccount, SystemLog
from apps.api.core import bybit as bybit_client
from apps.api.core.config import settings

logger = logging.getLogger(__name__)

def _notify_sync(text: str):
    try:
        from services.telegram_bot.telegram_service import emit_notification
        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(emit_notification(text))
    except Exception as e:
        logger.error(f"Failed to queue notification: {e}")


class LiveTradingEngine:
    """
    Executes real orders on Bybit via API and records them in the local database.
    Syncs balances and positions from the live exchange.
    """

    @staticmethod
    def _get_account(db: Session, user_id: int) -> Optional[ExchangeAccount]:
        return db.query(ExchangeAccount).filter(
            ExchangeAccount.user_id == user_id,
            ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
        ).first()

    # ------------------------------------------------------------------
    # Sync balance from Bybit → DB
    # ------------------------------------------------------------------
    @staticmethod
    def sync_balance(db: Session, account: ExchangeAccount) -> Dict[str, Any]:
        """Pull real balance from Bybit and persist to DB."""
        if account.exchange_name == "paper":
            bals = db.query(Balance).filter(Balance.account_id == account.id).all()
            return {b.asset: {"free": b.free, "locked": b.locked, "total": b.free + b.locked} for b in bals}

        live_balances = bybit_client.get_live_balance(account.api_key, account.api_secret)

        synced = {}
        for coin, data in live_balances.items():
            bal = db.query(Balance).filter(
                Balance.account_id == account.id,
                Balance.asset == coin
            ).first()
            if bal:
                bal.free   = data["free"]
                bal.locked = data["locked"]
                bal.updated_at = datetime.utcnow()
            else:
                bal = Balance(
                    account_id=account.id,
                    asset=coin,
                    free=data["free"],
                    locked=data["locked"],
                )
                db.add(bal)
            synced[coin] = data
        db.commit()
        return synced

    # ------------------------------------------------------------------
    # Sync positions from Bybit → DB
    # ------------------------------------------------------------------
    @staticmethod
    def sync_positions(db: Session, account: ExchangeAccount) -> list:
        """Pull open positions from Bybit and persist to DB."""
        if account.exchange_name == "paper":
            positions = db.query(Position).filter(Position.account_id == account.id).all()
            return [{"symbol": p.symbol, "side": p.side, "size": p.size, "entry_price": p.entry_price, "unrealized_pnl": p.unrealized_pnl} for p in positions]

        live_positions = bybit_client.get_live_positions(account.api_key, account.api_secret)

        # Detect closed positions before deleting
        old_positions = db.query(Position).filter(Position.account_id == account.id).all()
        live_symbols = {p["symbol"] for p in live_positions}
        
        for old_p in old_positions:
            if old_p.symbol not in live_symbols:
                # Position was closed! Let's notify.
                pnl_ind = "🟢 Profit" if old_p.unrealized_pnl >= 0 else "🔴 Loss"
                _notify_sync(
                    f"🏁 <b>Position Closed</b>\n"
                    f"• Symbol: <code>{old_p.symbol}</code>\n"
                    f"• Side: <b>{old_p.side}</b>\n"
                    f"• Result: {pnl_ind}\n"
                    f"• Est. PnL: <code>${old_p.unrealized_pnl:,.2f}</code>"
                )

        # Delete stale local positions
        db.query(Position).filter(Position.account_id == account.id).delete()

        synced = []
        for pos in live_positions:
            db_pos = Position(
                account_id=account.id,
                symbol=pos["symbol"],
                side="LONG" if pos["side"] == "Buy" else "SHORT",
                size=pos["size"],
                entry_price=pos["entry_price"],
                unrealized_pnl=pos["unrealized_pnl"],
            )
            db.add(db_pos)
            synced.append(pos)
        db.commit()
        return synced

    # ------------------------------------------------------------------
    # Execute a live order on Bybit
    # ------------------------------------------------------------------
    @staticmethod
    def execute_live_order(
        db: Session,
        account: ExchangeAccount,
        symbol: str,
        side: str,         # "BUY" or "SELL"
        qty: float,
        stop_loss_price: float = None,
        take_profit_price: float = None,
    ) -> Dict[str, Any]:
        """
        1. Gets current price
        2. Places real order on Bybit with SL/TP
        3. Records Order + Trade in local DB
        """
        # Bybit API uses "Buy"/"Sell"
        bybit_side = "Buy" if side.upper() in ["BUY", "LONG"] else "Sell"

        # Fetch live price for records
        current_price = bybit_client.get_live_price(symbol)
        if not current_price:
            return {"error": f"Could not fetch live price for {symbol}"}

        logger.info(f"Placing LIVE {bybit_side} order: {qty} {symbol} @ ~${current_price:,.2f}")

        if account.exchange_name == "paper":
            # Paper trading - mock the result
            result = {"order_id": f"paper_{int(datetime.utcnow().timestamp())}"}
            
            # Deduct balance
            trade_value = qty * current_price
            from shared.db.models import Balance
            b = db.query(Balance).filter(Balance.account_id == account.id, Balance.asset == "USDT").first()
            if b:
                b.free -= trade_value
                db.commit()
                
            # Update Position
            p = db.query(Position).filter(Position.account_id == account.id, Position.symbol == symbol).first()
            if not p:
                p = Position(account_id=account.id, symbol=symbol, side=side.upper(), size=qty, entry_price=current_price, unrealized_pnl=0.0)
                db.add(p)
            else:
                p.size += qty
                p.entry_price = (p.entry_price + current_price) / 2 # simplified avg entry
            db.commit()

        else:
            # Place real order
            result = bybit_client.place_live_order(
                api_key=account.api_key,
                api_secret=account.api_secret,
                symbol=symbol,
                side=bybit_side,
                qty=qty,
                stop_loss=stop_loss_price,
                take_profit=take_profit_price,
            )

        if "error" in result:
            LiveTradingEngine._log(db, "ERROR", "live_engine",
                                   f"Order failed: {result['error']}", {"symbol": symbol})
            _notify_sync(f"❌ <b>Trade Execution Failed</b>\nSymbol: <code>{symbol}</code>\nError: <code>{result['error']}</code>")
            return result

        # Record in local DB
        order = Order(
            account_id=account.id,
            symbol=symbol,
            order_type="MARKET",
            side=side.upper(),
            price=current_price,
            amount=qty,
            status="FILLED",
        )
        db.add(order)

        fee_rate = 0.0006  # Bybit taker fee 0.06%
        fee = qty * current_price * fee_rate
        trade = Trade(
            account_id=account.id,
            symbol=symbol,
            side=side.upper(),
            price=current_price,
            amount=qty,
            fee=fee,
        )
        db.add(trade)

        LiveTradingEngine._log(db, "INFO", "live_engine",
                               f"Live {bybit_side} executed: {qty} {symbol} @ ${current_price:,.4f}",
                               {
                                   "order_id": result.get("order_id"),
                                   "sl": stop_loss_price,
                                   "tp": take_profit_price,
                               })
        db.commit()

        _notify_sync(
            f"🚀 <b>Trade Executed!</b>\n"
            f"• Pair: <code>{symbol}</code>\n"
            f"• Action: <b>{side.upper()}</b>\n"
            f"• Entry Price: <code>${current_price:,.4f}</code>\n"
            f"• Size: <code>{qty}</code>\n"
            f"• SL: <code>${stop_loss_price:,.4f}</code>\n"
            f"• TP: <code>${take_profit_price:,.4f}</code>\n"
            f"• Leverage: 5x"
        )

        return {
            "status": "success",
            "bybit_order_id": result.get("order_id"),
            "symbol": symbol,
            "side": side.upper(),
            "qty": qty,
            "executed_price": current_price,
            "fee_est": round(fee, 4),
            "stop_loss": stop_loss_price,
            "take_profit": take_profit_price,
        }

    # ------------------------------------------------------------------
    # Calculate position size from risk %
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_qty(
        balance_usdt: float,
        risk_pct: float,
        price: float,
        min_qty: float = 0.001,
    ) -> float:
        """
        Risk pct of USDT balance ÷ price = qty in base currency.
        Rounded to 3 decimal places (suitable for BTC, ETH etc).
        """
        trade_value = balance_usdt * (risk_pct / 100.0)
        qty = trade_value / price
        qty = max(round(qty, 3), min_qty)
        return qty

    # ------------------------------------------------------------------
    # Log helper
    # ------------------------------------------------------------------
    @staticmethod
    def _log(db: Session, level: str, component: str, message: str, details: dict = None):
        try:
            log = SystemLog(level=level, component=component, message=message, details=details)
            db.add(log)
        except Exception:
            pass

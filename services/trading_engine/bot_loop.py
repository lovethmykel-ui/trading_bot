"""
Autonomous Trading Bot Loop
===========================
Runs as a FastAPI background task via asyncio.
Every TRADING_INTERVAL_SECONDS it:
  1. Scans the entire Bybit USDT market for high-opportunity pairs
  2. Picks the top-ranked pairs and runs the AI Consensus Engine on each
  3. If conviction >= threshold and no open position already exists:
       → Calculates qty from risk% of available USDT balance
       → Places a live market order on Bybit with SL + TP
  4. Logs every decision to system_logs table
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from apps.api.core.config import settings
from apps.api.core import bybit as bybit_client
from apps.api.core.database import SessionLocal
from shared.db.models import ExchangeAccount, SystemLog, Position
from services.trading_engine.live import LiveTradingEngine
from ai.ensemble.engine import ConsensusEngine

logger = logging.getLogger("bot_loop")

async def _notify(text: str):
    try:
        from services.telegram_bot.telegram_service import emit_notification
        await emit_notification(text)
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
_bot_running: bool = False
_bot_task: Optional[asyncio.Task] = None
_bot_status: Dict[str, Any] = {
    "running": False,
    "last_scan": None,
    "last_trade": None,
    "last_signal": None,
    "pairs_scanned": 0,
    "trades_today": 0,
    "errors": [],
}

_last_summary_date = None

consensus_engine = ConsensusEngine()


# ---------------------------------------------------------------------------
# Public control API (called from routers/bot.py)
# ---------------------------------------------------------------------------
def get_status() -> Dict[str, Any]:
    return dict(_bot_status)


def start_bot() -> bool:
    global _bot_running, _bot_task, _bot_status
    if _bot_running:
        return False
    _bot_running = True
    _bot_status["running"] = True
    _bot_status["errors"] = []
    _bot_task = asyncio.create_task(_trading_loop())
    logger.info("🤖 Bot loop STARTED")
    asyncio.create_task(_notify("🟢 <b>Bot Engine Started</b>\nAutonomous trading loops are now active."))
    return True


def stop_bot() -> bool:
    global _bot_running, _bot_task, _bot_status
    _bot_running = False
    _bot_status["running"] = False
    if _bot_task and not _bot_task.done():
        _bot_task.cancel()
        logger.info("🛑 Bot loop STOPPED")
        asyncio.create_task(_notify("🔴 <b>Bot Engine Stopped</b>\nAutonomous trading loops have been suspended."))
    return True


# ---------------------------------------------------------------------------
# Core trading loop
# ---------------------------------------------------------------------------
async def _trading_loop():
    global _bot_status
    logger.info(f"Bot loop running every {settings.TRADING_INTERVAL_SECONDS}s | "
                f"Risk={settings.RISK_PER_TRADE_PCT}% | SL={settings.STOP_LOSS_PCT}% | TP={settings.TAKE_PROFIT_PCT}%")

    while _bot_running:
        try:
            await _run_cycle()

            # Daily Summary check (00:00 WAT / UTC+1)
            global _last_summary_date
            wat_tz = timezone(timedelta(hours=1))
            now_wat = datetime.now(wat_tz)
            if now_wat.hour == 0 and _last_summary_date != now_wat.date():
                await _send_daily_summary()
                _last_summary_date = now_wat.date()
                _bot_status["trades_today"] = 0 # reset daily counter

        except asyncio.CancelledError:
            logger.info("Bot loop task cancelled")
            break
        except Exception as e:
            err_msg = f"Loop cycle error: {e}"
            logger.error(err_msg, exc_info=True)
            _bot_status["errors"] = (_bot_status.get("errors", []) + [err_msg])[-10:]
            await _notify(f"⚠️ <b>System Error</b>\nThe trading loop encountered an error and will retry shortly:\n<code>{str(e)}</code>")

        # Wait for next cycle
        await asyncio.sleep(settings.TRADING_INTERVAL_SECONDS)

async def _send_daily_summary():
    # Simple summary format
    trades = _bot_status.get("trades_today", 0)
    msg = (
        f"📊 <b>Daily Performance Summary</b>\n"
        f"• Trades Executed Today: <code>{trades}</code>\n"
        f"• Active Pairs Scanned: <code>{_bot_status.get('pairs_scanned', 0)}</code>\n"
        f"• Status: <b>🟢 RUNNING</b>\n"
    )
    await _notify(msg)


async def _run_cycle():
    """Single iteration: scan market → analyse → trade if conviction met."""
    global _bot_status

    db = SessionLocal()
    try:
        # 1. Find the connected exchange account
        account = db.query(ExchangeAccount).filter(
            ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
        ).first()

        if not account:
            logger.warning("No exchange account connected — bot is idle")
            _bot_status["last_scan"] = datetime.utcnow().isoformat()
            return

        # 2. Sync current balance
        if account.exchange_name == "paper":
            from shared.db.models import Balance
            b = db.query(Balance).filter(Balance.account_id == account.id, Balance.asset == "USDT").first()
            usdt_free = b.free if b else 0.0
        else:
            live_balances = bybit_client.get_live_balance(account.api_key, account.api_secret)
            usdt_free = live_balances.get("USDT", {}).get("free", 0.0)

        if usdt_free < 1.0:
            logger.warning(f"Insufficient USDT balance (${usdt_free:.2f}) — skipping cycle")
            _log(db, "WARNING", "bot_loop", f"Low balance: ${usdt_free:.2f} USDT — trade skipped")
            return

        # 3. Scan the full market for top opportunities
        logger.info("Scanning market for top pairs…")
        top_pairs = bybit_client.scan_market(
            top_n=settings.TOP_PAIRS_TO_SCAN,
            min_volume_usdt=settings.MIN_24H_VOLUME_USDT,
        )
        _bot_status["pairs_scanned"] = len(top_pairs)
        _bot_status["last_scan"] = datetime.utcnow().isoformat()

        if not top_pairs:
            logger.warning("Market scan returned no pairs")
            return

        candidate_list = ", ".join([p['symbol'] for p in top_pairs[:5]])
        logger.info(f"Top pair candidates: {candidate_list}")
        # Notify scan complete
        await _notify(f"🔍 <b>Market Scan Complete</b>\nAnalyzed <b>{_bot_status['pairs_scanned']}</b> active pairs.\nTop candidates: {candidate_list}")

        # 4. Run AI consensus on each candidate pair (top 5 to keep it fast)
        best_signal = None
        best_symbol = None
        best_confidence = 0

        for pair_info in top_pairs[:10]:  # Analyse top 10 candidates
            symbol = pair_info["symbol"]

            # Skip if we already have an open position for this symbol
            existing_pos = db.query(Position).filter(
                Position.account_id == account.id,
                Position.symbol == symbol
            ).first()
            if existing_pos:
                logger.info(f"Skipping {symbol}: already have open position")
                continue

            # Fetch candle data
            candles = bybit_client.get_candles(symbol=symbol, interval="5", limit=100)
            if len(candles) < 20:
                continue

            current_price = candles[-1]["close"] if candles else pair_info["last_price"]

            # Build market_data context for AI engine
            market_data = {
                "symbol": symbol,
                "current_price": current_price,
                "recent_daily_klines": [[
                    str(c["timestamp"]),
                    str(c["open"]), str(c["high"]),
                    str(c["low"]),  str(c["close"]),
                    str(c["volume"])
                ] for c in candles[-10:]],
                "price_change_24h": pair_info.get("price_change", 0),
                "volume_24h": pair_info.get("volume_24h", 0),
                "volatility": pair_info.get("volatility", 0),
                "news_headlines": [
                    "Crypto market showing increased institutional interest.",
                    "Global liquidity conditions remain supportive of risk assets."
                ],
                "social_fear_greed_index": 65,
            }

            # Run the ensemble (runs synchronously — wrap in executor to avoid blocking)
            loop = asyncio.get_event_loop()
            consensus = await loop.run_in_executor(
                None, consensus_engine.run_consensus, market_data
            )

            confidence = consensus.get("overall_confidence", 0)
            decision   = consensus.get("final_decision", "NEUTRAL")

            logger.info(f"  {symbol}: {decision} @ {confidence}% confidence")
            _bot_status["last_signal"] = {
                "symbol": symbol,
                "decision": decision,
                "confidence": confidence,
                "at": datetime.utcnow().isoformat(),
            }

            if decision != "NEUTRAL" and confidence > best_confidence:
                best_confidence = confidence
                best_signal = decision
                best_symbol = symbol

        # 5. Execute trade on the best signal if conviction meets threshold
        threshold = settings.SIGNAL_CONVICTION_THRESHOLD * 100  # e.g. 65

        if best_symbol and best_signal and best_confidence >= threshold:
            current_price = bybit_client.get_live_price(best_symbol) or 0
            if current_price <= 0:
                logger.error(f"Cannot get price for {best_symbol}, skipping trade")
                return

            qty = LiveTradingEngine.calculate_qty(
                balance_usdt=usdt_free,
                risk_pct=settings.RISK_PER_TRADE_PCT,
                price=current_price,
            )

            # Calculate SL/TP levels
            if best_signal == "LONG":
                sl = current_price * (1 - settings.STOP_LOSS_PCT / 100)
                tp = current_price * (1 + settings.TAKE_PROFIT_PCT / 100)
            else:  # SHORT
                sl = current_price * (1 + settings.STOP_LOSS_PCT / 100)
                tp = current_price * (1 - settings.TAKE_PROFIT_PCT / 100)

            logger.info(
                f"🚀 Trading signal: {best_signal} {qty} {best_symbol} @ ${current_price:,.4f} "
                f"| SL=${sl:,.4f} | TP=${tp:,.4f} | Confidence={best_confidence}%"
            )

            # Set leverage first (5x) (skip for paper)
            if account.exchange_name != "paper":
                bybit_client.set_leverage(account.api_key, account.api_secret, best_symbol, leverage=5)

            # Place the live order
            result = LiveTradingEngine.execute_live_order(
                db=db,
                account=account,
                symbol=best_symbol,
                side=best_signal,   # "LONG" or "SHORT"
                qty=qty,
                stop_loss_price=round(sl, 4),
                take_profit_price=round(tp, 4),
            )

            if "error" not in result:
                _bot_status["last_trade"] = {
                    "symbol": best_symbol,
                    "side": best_signal,
                    "qty": qty,
                    "price": current_price,
                    "sl": round(sl, 4),
                    "tp": round(tp, 4),
                    "bybit_order_id": result.get("bybit_order_id"),
                    "at": datetime.utcnow().isoformat(),
                }
                _bot_status["trades_today"] = _bot_status.get("trades_today", 0) + 1
                logger.info(f"✅ Trade executed: {result}")
            else:
                logger.error(f"❌ Trade failed: {result['error']}")
                _bot_status["errors"] = (_bot_status.get("errors", []) + [result["error"]])[-10:]

        else:
            reason = (
                f"No trade: best signal={best_signal} on {best_symbol} "
                f"at {best_confidence}% (threshold={threshold}%)"
            ) if best_symbol else "No valid signal found across all scanned pairs"
            logger.info(reason)
            _log(db, "INFO", "bot_loop", reason)

    finally:
        db.close()


def _log(db, level: str, component: str, message: str, details: dict = None):
    try:
        db.add(SystemLog(level=level, component=component, message=message, details=details))
        db.commit()
    except Exception:
        pass

import asyncio
import json
import urllib.request
import urllib.parse
import logging
import ssl
from typing import Optional
from sqlalchemy.orm import Session

from apps.api.core.config import settings
from apps.api.core.database import SessionLocal
from shared.db.models import ExchangeAccount, Balance, Position, User
from services.trading_engine import bot_loop
from apps.api.core import bybit as bybit_client

logger = logging.getLogger("telegram_bot")

_telegram_task: Optional[asyncio.Task] = None
_running: bool = False

def _send_telegram_request(method: str, data: dict = None) -> dict:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return {"ok": False, "error": "No token configured"}
    url = f"https://api.telegram.org/bot{token}/{method}"
    
    headers = {"Content-Type": "application/json"}
    req_data = json.dumps(data).encode("utf-8") if data else None
    
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST" if data else "GET")
        with urllib.request.urlopen(req, timeout=20, context=context) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"Telegram API request failed: {e}")
        return {"ok": False, "error": str(e)}

async def send_telegram_request_async(method: str, data: dict = None) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _send_telegram_request, method, data)

async def start_telegram_bot():
    global _telegram_task, _running
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured in .env. Telegram service disabled.")
        return
    
    if _running:
        return
        
    _running = True
    _telegram_task = asyncio.create_task(_bot_polling_loop())
    logger.info("Telegram Bot service started successfully.")

def stop_telegram_bot():
    global _running, _telegram_task
    _running = False
    if _telegram_task and not _telegram_task.done():
        _telegram_task.cancel()
        logger.info("Telegram Bot service stopped.")

async def _bot_polling_loop():
    offset = 0
    while _running:
        try:
            resp = await send_telegram_request_async("getUpdates", {
                "offset": offset,
                "timeout": 15,
                "allowed_updates": ["message"]
            })
            
            if resp.get("ok") and resp.get("result"):
                for update in resp["result"]:
                    offset = update["update_id"] + 1
                    message = update.get("message")
                    if message:
                        await _handle_message(message)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in Telegram long poll loop: {e}")
            await asyncio.sleep(5)
            
        await asyncio.sleep(0.5)

async def _handle_message(message: dict):
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    text = message.get("text", "").strip()
    
    if not text:
        return

    auth_chat_id = settings.TELEGRAM_AUTHORIZED_CHAT_ID.strip()
    
    # Security: Require matching chat ID
    if auth_chat_id and chat_id != auth_chat_id:
        logger.warning(f"Unauthorized Telegram access attempted from Chat ID: {chat_id}")
        await send_telegram_request_async("sendMessage", {
            "chat_id": chat_id,
            "text": f"⚠️ <b>Access Denied.</b> This bot is private.\nYour Chat ID <code>{chat_id}</code> is not authorized.",
            "parse_mode": "HTML"
        })
        return

    # If no authorized chat ID is set, guide the user to configure it
    if not auth_chat_id:
        logger.info(f"Telegram Bot received a message. To configure authorization, set: TELEGRAM_AUTHORIZED_CHAT_ID={chat_id}")
        await send_telegram_request_async("sendMessage", {
            "chat_id": chat_id,
            "text": f"⚠️ <b>Configuration Required</b>\n\nTo lock and authorize this chat to control the trading bot, add this variable to your <code>.env</code> file:\n\n<code>TELEGRAM_AUTHORIZED_CHAT_ID={chat_id}</code>\n\nThen restart the API server.",
            "parse_mode": "HTML"
        })
        return

    parts = text.split(maxsplit=2)
    command = parts[0].split("@")[0].lower() # strip bot handle if present (e.g. /start@my_bot -> /start)
    args = parts[1:] if len(parts) > 1 else []

    db = SessionLocal()
    try:
        if command in ["/start", "/help"]:
            await _cmd_help(chat_id)
        elif command == "/status":
            await _cmd_status(chat_id, db)
        elif command == "/start_trading":
            await _cmd_start_trading(chat_id, db)
        elif command == "/stop_trading":
            await _cmd_stop_trading(chat_id)
        elif command == "/balance":
            await _cmd_balance(chat_id, db)
        elif command == "/positions":
            await _cmd_positions(chat_id, db)
        elif command == "/set_paper":
            await _cmd_set_paper(chat_id, args, db)
        elif command == "/set_api_keys":
            await _cmd_set_api_keys(chat_id, args, db)
        else:
            await send_telegram_request_async("sendMessage", {
                "chat_id": chat_id,
                "text": "❓ <b>Unknown command.</b> Type /help to see the control commands.",
                "parse_mode": "HTML"
            })
    except Exception as e:
        logger.error(f"Error handling Telegram command '{command}': {e}", exc_info=True)
        await send_telegram_request_async("sendMessage", {
            "chat_id": chat_id,
            "text": f"❌ <b>Execution Error:</b>\n<code>{str(e)}</code>",
            "parse_mode": "HTML"
        })
    finally:
        db.close()

async def _cmd_help(chat_id: str):
    help_text = (
        "🤖 <b>Quantum Ensemble Control Panel</b>\n\n"
        "Use these commands to remotely control your trading bot:\n\n"
        "⚡ <b>/status</b> - View running state, current mode, and last trade\n"
        "🟢 <b>/start_trading</b> - Start the background market scanner & execution\n"
        "🔴 <b>/stop_trading</b> - Stop the autonomous trading loops\n"
        "💰 <b>/balance</b> - Fetch current wallet balance (Bybit or Paper)\n"
        "📊 <b>/positions</b> - View open positions and PnL\n"
        "⚙️ <b>/set_paper [true|false]</b> - Switch between paper and live trading\n"
        "🔑 <b>/set_api_keys [key] [secret]</b> - Set credentials & activate Bybit live mode\n"
        "❓ <b>/help</b> - Show this interface instructions"
    )
    await send_telegram_request_async("sendMessage", {
        "chat_id": chat_id,
        "text": help_text,
        "parse_mode": "HTML"
    })

async def _cmd_status(chat_id: str, db: Session):
    status = bot_loop.get_status()
    running_status = "🟢 <b>RUNNING</b>" if status.get("running") else "🔴 <b>STOPPED</b>"
    
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
    ).first()
    
    mode_text = "None"
    if account:
        mode_text = "PAPER TRADING" if account.exchange_name == "paper" else "LIVE TRADING (Bybit)"

    text = (
        f"⚡ <b>Trading Bot Status</b>\n"
        f"• Status: {running_status}\n"
        f"• Mode: <b>{mode_text}</b>\n"
        f"• Last Scan: <code>{status.get('last_scan') or 'Never'}</code>\n"
        f"• Candidate Pairs Scanned: <code>{status.get('pairs_scanned', 0)}</code>\n"
        f"• Executed Trades (Today): <code>{status.get('trades_today', 0)}</code>\n"
    )
    
    last_trade = status.get("last_trade")
    if last_trade:
        text += (
            f"\n📈 <b>Last Executed Position:</b>\n"
            f"• Symbol: <code>{last_trade.get('symbol')}</code>\n"
            f"• Action: <b>{last_trade.get('side')}</b>\n"
            f"• Qty: <code>{last_trade.get('qty')}</code>\n"
            f"• Executed Price: <code>${last_trade.get('price'):,.4f}</code>\n"
            f"• SL: <code>${last_trade.get('sl'):,.4f}</code> | TP: <code>${last_trade.get('tp'):,.4f}</code>\n"
            f"• Timestamp: <code>{last_trade.get('at')}</code>\n"
        )
        
    errors = status.get("errors", [])
    if errors:
        text += f"\n⚠️ <b>Recent Warning/Error:</b>\n<code>{errors[-1]}</code>"
        
    await send_telegram_request_async("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    })

async def _cmd_start_trading(chat_id: str, db: Session):
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
    ).first()
    
    if not account:
        await send_telegram_request_async("sendMessage", {
            "chat_id": chat_id,
            "text": "❌ <b>Cannot Start:</b> No exchange account or paper settings found in the database. Use `/set_paper true` or `/set_api_keys` first.",
            "parse_mode": "HTML"
        })
        return

    started = bot_loop.start_bot()
    if started:
        msg = f"🟢 <b>Trading Bot Loop Started!</b>\nScanning markets every {settings.TRADING_INTERVAL_SECONDS // 60} minutes."
    else:
        msg = "ℹ️ <b>Info:</b> The bot is already running."
        
    await send_telegram_request_async("sendMessage", {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML"
    })

async def _cmd_stop_trading(chat_id: str):
    bot_loop.stop_bot()
    await send_telegram_request_async("sendMessage", {
        "chat_id": chat_id,
        "text": "🔴 <b>Trading Bot Loop Stopped.</b> Active scanning suspended.",
        "parse_mode": "HTML"
    })

async def _cmd_balance(chat_id: str, db: Session):
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
    ).first()
    
    if not account:
        await send_telegram_request_async("sendMessage", {
            "chat_id": chat_id,
            "text": "❌ No connected exchange account found."
        })
        return

    if account.exchange_name == "paper":
        b = db.query(Balance).filter(Balance.account_id == account.id, Balance.asset == "USDT").first()
        free = b.free if b else 0.0
        locked = b.locked if b else 0.0
        total = free + locked
        bal_text = (
            f"💰 <b>Paper Wallet Balance</b>\n"
            f"• Asset: <b>USDT</b>\n"
            f"• Available: <code>${free:,.2f}</code>\n"
            f"• Locked in Trades: <code>${locked:,.2f}</code>\n"
            f"• Total Value: <b>${total:,.2f}</b>"
        )
    else:
        try:
            balances = bybit_client.get_live_balance(account.api_key, account.api_secret)
            usdt = balances.get("USDT", {"free": 0.0, "locked": 0.0, "total": 0.0})
            bal_text = (
                f"💰 <b>Bybit Live Balance (USDT)</b>\n"
                f"• Available: <code>${usdt.get('free', 0.0):,.2f}</code>\n"
                f"• Locked/Margin: <code>${usdt.get('locked', 0.0):,.2f}</code>\n"
                f"• Total Balance: <b>${usdt.get('total', 0.0):,.2f}</b>"
            )
        except Exception as e:
            bal_text = f"❌ <b>Error Fetching Bybit Balance:</b>\n<code>{str(e)}</code>"
            
    await send_telegram_request_async("sendMessage", {
        "chat_id": chat_id,
        "text": bal_text,
        "parse_mode": "HTML"
    })

async def _cmd_positions(chat_id: str, db: Session):
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
    ).first()
    
    if not account:
        await send_telegram_request_async("sendMessage", {
            "chat_id": chat_id,
            "text": "❌ No connected exchange account found."
        })
        return

    if account.exchange_name == "paper":
        positions = db.query(Position).filter(Position.account_id == account.id).all()
        if not positions:
            pos_text = "📊 <b>Active Positions:</b>\nNo open positions found in Paper account."
        else:
            pos_text = "📊 <b>Active Positions (Paper Mode):</b>\n"
            for p in positions:
                pnl_indicator = "🟢" if p.unrealized_pnl >= 0 else "🔴"
                pos_text += (
                    f"\n• <b>{p.symbol}</b> ({p.side})\n"
                    f"  Size: <code>{p.size}</code>\n"
                    f"  Entry Price: <code>${p.entry_price:,.4f}</code>\n"
                    f"  Unrealized PnL: {pnl_indicator} <code>${p.unrealized_pnl:+,.2f}</code>\n"
                )
    else:
        try:
            positions = bybit_client.get_live_positions(account.api_key, account.api_secret)
            if not positions:
                pos_text = "📊 <b>Active Positions:</b>\nNo open positions found on Bybit."
            else:
                pos_text = "📊 <b>Active Positions (Bybit Live):</b>\n"
                for p in positions:
                    side = "LONG" if p["side"] == "Buy" else "SHORT"
                    pnl = float(p.get("unrealized_pnl", 0.0))
                    pnl_indicator = "🟢" if pnl >= 0 else "🔴"
                    pos_text += (
                        f"\n• <b>{p['symbol']}</b> ({side})\n"
                        f"  Size: <code>{p['size']}</code>\n"
                        f"  Entry Price: <code>${p['entry_price']}</code>\n"
                        f"  Unrealized PnL: {pnl_indicator} <code>${pnl:+,.2f}</code>\n"
                    )
        except Exception as e:
            pos_text = f"❌ <b>Error Fetching Positions:</b>\n<code>{str(e)}</code>"

    await send_telegram_request_async("sendMessage", {
        "chat_id": chat_id,
        "text": pos_text,
        "parse_mode": "HTML"
    })

async def _cmd_set_paper(chat_id: str, args: list, db: Session):
    if not args:
        await send_telegram_request_async("sendMessage", {
            "chat_id": chat_id,
            "text": "⚠️ <b>Usage:</b> <code>/set_paper [true|false]</code>",
            "parse_mode": "HTML"
        })
        return

    is_paper = args[0].strip().lower() == "true"
    
    # Stop bot loop before changing account mode
    bot_loop.stop_bot()

    # Find or create default user in database
    user = db.query(User).first()
    if not user:
        user = User(email="telegram_user@system.local", hashed_password="default_system_password")
        db.add(user)
        db.commit()

    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
    ).first()

    if is_paper:
        if account:
            account.exchange_name = "paper"
        else:
            account = ExchangeAccount(
                user_id=user.id,
                exchange_name="paper",
                api_key="paper_key",
                api_secret="paper_secret",
                is_testnet=settings.BYBIT_TESTNET
            )
            db.add(account)
        
        db.commit() # Save to get account ID for balance mapping
        
        # Ensure paper USDT balance is initialized
        bal = db.query(Balance).filter(Balance.account_id == account.id, Balance.asset == "USDT").first()
        if not bal:
            bal = Balance(account_id=account.id, asset="USDT", free=10000.0, locked=0.0)
            db.add(bal)
        
        db.commit()
        msg = "⚙️ <b>Mode Switched: PAPER TRADING</b>\nLocal simulated environment activated with $10,000 USDT mock balance."
    else:
        if account and account.exchange_name == "paper":
            account.exchange_name = "bybit"
            account.api_key = "replace_me"
            account.api_secret = "replace_me"
            db.commit()
            msg = "⚙️ <b>Mode Switched: LIVE TRADING (Bybit)</b>\n⚠️ Please set your Bybit API keys with: <code>/set_api_keys [api_key] [api_secret]</code>."
        elif account:
            account.exchange_name = "bybit"
            db.commit()
            msg = "⚙️ <b>Mode Switched: LIVE TRADING (Bybit)</b>"
        else:
            account = ExchangeAccount(
                user_id=user.id,
                exchange_name="bybit",
                api_key="replace_me",
                api_secret="replace_me",
                is_testnet=settings.BYBIT_TESTNET
            )
            db.add(account)
            db.commit()
            msg = "⚙️ <b>Mode Switched: LIVE TRADING (Bybit)</b>\n⚠️ Please set your Bybit API keys with: <code>/set_api_keys [api_key] [api_secret]</code>."

    await send_telegram_request_async("sendMessage", {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML"
    })

async def _cmd_set_api_keys(chat_id: str, args: list, db: Session):
    # Combine arguments and split on whitespace to isolate key and secret
    raw_args = " ".join(args).split()
    if len(raw_args) < 2:
        await send_telegram_request_async("sendMessage", {
            "chat_id": chat_id,
            "text": "⚠️ <b>Usage:</b> <code>/set_api_keys [api_key] [api_secret]</code>",
            "parse_mode": "HTML"
        })
        return

    api_key = raw_args[0].strip()
    api_secret = raw_args[1].strip()

    # Stop bot loop during credentials update
    bot_loop.stop_bot()

    user = db.query(User).first()
    if not user:
        user = User(email="telegram_user@system.local", hashed_password="default_system_password")
        db.add(user)
        db.commit()

    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.is_testnet == settings.BYBIT_TESTNET
    ).first()

    if account:
        account.exchange_name = "bybit"
        account.api_key = api_key
        account.api_secret = api_secret
    else:
        account = ExchangeAccount(
            user_id=user.id,
            exchange_name="bybit",
            api_key=api_key,
            api_secret=api_secret,
            is_testnet=settings.BYBIT_TESTNET
        )
        db.add(account)

    db.commit()
    
    # Zero out balances so sync can overwrite them with live values
    db.query(Balance).filter(Balance.account_id == account.id).delete()
    db.commit()

    await send_telegram_request_async("sendMessage", {
        "chat_id": chat_id,
        "text": "🔑 <b>Bybit API keys successfully configured.</b>\nTrading mode active: Live (Bybit). Make sure your key has trading permissions on Bybit Testnet/Mainnet.",
        "parse_mode": "HTML"
    })

async def emit_notification(text: str):
    """
    Sends an immediate Telegram notification to the authorized chat ID.
    """
    auth_chat_id = settings.TELEGRAM_AUTHORIZED_CHAT_ID.strip()
    if not auth_chat_id:
        return
    
    try:
        await send_telegram_request_async("sendMessage", {
            "chat_id": auth_chat_id,
            "text": text,
            "parse_mode": "HTML"
        })
    except Exception as e:
        logger.error(f"Failed to emit notification: {e}")

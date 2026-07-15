from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.core.config import settings
from apps.api.routers import auth, exchange, market, orders, portfolio, settings as system_settings, system, ws, ai, bot


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler.
    On startup: Bot is available but NOT auto-started (user must click Start in UI).
    On shutdown: Gracefully stop the bot loop.
    """
    print(f"[START] {settings.PROJECT_NAME} API started.")
    print(f"   Testnet: {settings.BYBIT_TESTNET}")
    print(f"   Risk per trade: {settings.RISK_PER_TRADE_PCT}%")
    print(f"   Scan interval: {settings.TRADING_INTERVAL_SECONDS}s")
    
    # Start Telegram Command Center bot listener task
    from services.telegram_bot.telegram_service import start_telegram_bot
    await start_telegram_bot()
    
    yield
    # Cleanup on shutdown
    from services.trading_engine.bot_loop import stop_bot
    from services.telegram_bot.telegram_service import stop_telegram_bot
    stop_bot()
    stop_telegram_bot()
    print("Bot loops and services stopped. Server shutting down.")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In prod, allow only frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,           prefix="/auth",      tags=["auth"])
app.include_router(exchange.router,       prefix="/exchange",  tags=["exchange"])
app.include_router(market.router,         prefix="/market",    tags=["market"])
app.include_router(portfolio.router,      prefix="/portfolio", tags=["portfolio"])
app.include_router(orders.router,         prefix="/orders",    tags=["orders"])
app.include_router(system.router,         prefix="/system",    tags=["system"])
app.include_router(system_settings.router, prefix="/settings", tags=["settings"])
app.include_router(ai.router,             prefix="/ai",        tags=["ai"])
app.include_router(bot.router,            prefix="/bot",       tags=["bot"])
app.include_router(ws.router,             tags=["websocket"])


@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "testnet": settings.BYBIT_TESTNET,
        "docs": "/docs",
    }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.core.config import settings
from apps.api.routers import auth, exchange, market, orders, portfolio, settings as system_settings, system, ws, ai

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In prod, allow only frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(exchange.router, prefix="/exchange", tags=["exchange"])
app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(system.router, prefix="/system", tags=["system"])
app.include_router(system_settings.router, prefix="/settings", tags=["settings"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(ws.router, tags=["websocket"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

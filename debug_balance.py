"""
Debug script: prints the raw Bybit balance response so we can see 
exactly which fields contain the USDT amount.
Run from the project root:  .venv\Scripts\python debug_balance.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.api.core.database import SessionLocal
from shared.db.models import ExchangeAccount

db = SessionLocal()
account = db.query(ExchangeAccount).first()

if not account:
    print("ERROR: No exchange account found in DB. Connect your API keys first via Settings.")
    sys.exit(1)

print(f"Found account: id={account.id}, testnet={account.is_testnet}")
print(f"API key (first 6): {account.api_key[:6]}...")

# Import AFTER setting up path
from pybit.unified_trading import HTTP
from apps.api.core import bybit as bc

session = bc.get_bybit_client(account.api_key, account.api_secret)
resp = session.get_wallet_balance(accountType="UNIFIED")

print("\n=== RAW BYBIT RESPONSE ===")
print(json.dumps(resp, indent=2))

print("\n=== PARSED by get_live_balance() ===")
parsed = bc.get_live_balance(account.api_key, account.api_secret)
print(json.dumps(parsed, indent=2))

usdt = parsed.get("USDT", {})
print(f"\n=== USDT Summary ===")
print(f"  free   : {usdt.get('free', 0)}")
print(f"  locked : {usdt.get('locked', 0)}")
print(f"  total  : {usdt.get('total', 0)}")
print(f"  usd_val: {usdt.get('usd_value', 0)}")

db.close()

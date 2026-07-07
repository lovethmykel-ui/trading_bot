from pybit.unified_trading import HTTP
from apps.api.core.config import settings

def get_bybit_client(api_key: str = None, api_secret: str = None):
    # Initializes a Bybit client
    return HTTP(
        testnet=settings.BYBIT_TESTNET,
        api_key=api_key,
        api_secret=api_secret,
    )

def test_connection(api_key: str, api_secret: str):
    try:
        session = get_bybit_client(api_key, api_secret)
        # Call a lightweight endpoint to test
        response = session.get_wallet_balance(accountType="UNIFIED", coin="USDT")
        return True, response
    except Exception as e:
        return False, str(e)

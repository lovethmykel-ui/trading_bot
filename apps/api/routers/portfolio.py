from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_portfolio():
    return {
        "status": "success",
        "data": {
            "total_value": 0.0,
            "todays_pnl": 0.0,
            "win_rate": 0.0,
            "open_positions_count": 0,
            "balances": []
        }
    }

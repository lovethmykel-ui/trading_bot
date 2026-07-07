from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_system_status():
    return {
        "status": "success",
        "health": {
            "api": "OK",
            "websocket": "OK",
            "database": "OK"
        }
    }

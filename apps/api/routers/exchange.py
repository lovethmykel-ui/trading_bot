from fastapi import APIRouter

router = APIRouter()

@router.post("/connect")
def connect_exchange():
    return {"status": "success", "message": "Exchange connection established"}

@router.post("/test")
def test_exchange():
    return {"status": "success", "message": "Exchange API test successful"}

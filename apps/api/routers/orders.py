from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_orders():
    return {"status": "success", "data": []}

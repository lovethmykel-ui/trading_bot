from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_settings():
    return {"status": "success", "data": {"theme": "dark", "notifications": True}}

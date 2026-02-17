from fastapi import APIRouter
from app.schemas import BoolResponse

router = APIRouter()


@router.get("/check/", response_model=BoolResponse)
async def get_connected():
    """ Проверка связи с API сервером """
    return True

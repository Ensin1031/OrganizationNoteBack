from fastapi import APIRouter

from app.routes.root import router as root_router
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router

router = APIRouter()

# Подключаем роутеры
router.include_router(root_router)
router.include_router(auth_router)
router.include_router(users_router)

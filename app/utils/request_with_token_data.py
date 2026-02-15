from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from app.settings import settings
from app.utils.token_manager import TokenManager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.root_path}/auth/login/")


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
):
    token_manager = TokenManager(settings.secret_key)
    if not token_manager.verify_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизированный пользователь. Доступ закрыт"
        )

    data = token_manager.decode_token(token)
    return data.get("user_id")

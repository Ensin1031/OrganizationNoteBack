from datetime import datetime, timezone, timedelta

import jwt
from app.db.models import User


class TokenManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 24 * 60

    def create_access_token(self, token_data: dict = {}):
        expired_at = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        data = {
            **token_data,
            "exp": int(expired_at.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp())
        }

        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str):
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    "verify_exp": True
                }
            )
        except Exception:
            return None

    def verify_token(self, token: str) -> bool:
        if token is None:
            return False

        try:
            data = self.decode_token(token)
            has_token_user = User.has_user_by_id(user_id=data.get("user_id", None))
            exp = datetime.fromtimestamp(data.get('exp'), tz=timezone.utc)
            iat = datetime.fromtimestamp(data.get('iat'), tz=timezone.utc)
            now = datetime.now(timezone.utc)
            token_is_not_expired = iat < now < exp

            return data is not None and has_token_user and token_is_not_expired
        except Exception:
            return False

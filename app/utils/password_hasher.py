import hashlib
import secrets

import jwt

from app.settings import settings


def create_token(user_id: int):
    payload = {"user_id": user_id}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.a)


class PasswordHasher:

    @staticmethod
    def generate_salt():
        return secrets.token_hex(16)

    @staticmethod
    def hash_password(password: str, salt: str):
        return hashlib.sha256((password + salt).encode()).hexdigest()

    @staticmethod
    def verify_password(input_password: str, stored_hash: str, salt: str):
        return hashlib.sha256((input_password + salt).encode()).hexdigest() == stored_hash

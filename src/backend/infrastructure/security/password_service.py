import asyncio

import bcrypt


class PasswordService:
    """Хеширование паролей и их проверка"""

    async def hash_password(self, plain_password: str) -> str:
        """Возвращает хеш пароля"""
        return await asyncio.to_thread(self._hash_sync, plain_password)

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверяет соответствие пароля и хеша"""
        return await asyncio.to_thread(
            self._verify_sync, plain_password, hashed_password
        )

    def _hash_sync(self, plain_password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def _verify_sync(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

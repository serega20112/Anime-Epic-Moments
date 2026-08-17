import asyncio

import bcrypt


class PasswordService:
    """Хеширование паролей и их проверка"""

    async def hash_password(self, plain_password: str) -> str:
        """Возвращает хеш пароля"""
        return await asyncio.to_thread(
            lambda: bcrypt.hashpw(
                plain_password.encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("utf-8")
        )

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверяет соответствие пароля и хеша"""
        return await asyncio.to_thread(
            lambda: bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        )

import bcrypt


class PasswordService:
    """Хеширование паролей и их проверка"""

    def hash_password(self, plain_password: str) -> str:
        """Возвращает хеш пароля"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверяет соответствие пароля и хеша"""
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

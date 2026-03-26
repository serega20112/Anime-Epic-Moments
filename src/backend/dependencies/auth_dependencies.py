"""
auth_dependencies.py — DI зависимости для Auth
"""

from src.backend.infrastructure.security.password_service import PasswordService
from src.backend.infrastructure.security.jwt_service import JWTService

# Сервисы аутентификации / шифрования
password_service = PasswordService()
jwt_service = JWTService()


# Middleware (Flask decorator), чтобы проверять авторизацию
def auth_required(f):
    from functools import wraps
    from flask import request, jsonify

    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Authorization token required"}), 401

        try:
            user_id = jwt_service.decode_token(token)
        except Exception:
            return jsonify({"error": "Invalid or expired token"}), 401

        # прокидываем user_id в kwargs, чтобы use case мог его получить
        kwargs["user_id"] = user_id
        return f(*args, **kwargs)

    return decorated

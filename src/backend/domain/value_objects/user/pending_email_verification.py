"""Ожидающее подтверждение адреса почты."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PendingEmailVerification:
    """Код и срок действия подтверждения адреса почты."""

    email: str
    username: str
    password_hash: str
    code: str
    theme: str = "neon"

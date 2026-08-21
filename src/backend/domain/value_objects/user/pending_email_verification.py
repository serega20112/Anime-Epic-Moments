from dataclasses import dataclass


@dataclass
class PendingEmailVerification:
    email: str
    username: str
    password_hash: str
    code: str
    theme: str = "neon"

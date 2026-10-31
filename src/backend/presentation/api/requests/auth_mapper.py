"""Преобразование данных форм аутентификации в команды application."""

from __future__ import annotations

from backend.application.dto.auth import (
    ConfirmPasswordResetCommand,
    LoginCommand,
    RegisterCommand,
    RequestPasswordResetCommand,
    ResendVerificationCommand,
    UpdateProfileCommand,
    VerifyEmailCommand,
)
from backend.domain.aggregates.user.user import STATUS_MAX_LENGTH
from backend.domain.policies.email_verification_policy import normalize_theme
from backend.domain.policies.user_credentials_policy import normalize_email

EMAIL_MAX_LENGTH = 254
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
USERNAME_MAX_LENGTH = 20
VERIFICATION_CODE_DIGITS = 6


class FormValidationError(ValueError):
    """Ошибка проверки данных HTML-формы."""


def _field_text(form: dict, name: str) -> str:
    """Вернуть строковое поле формы без пробелов по краям.

    Args:
        form: Разобранные данные формы.
        name: Имя поля.

    Returns:
        str: Значение поля либо пустая строка.
    """
    return str(form.get(name) or "").strip()


def _extract_digits(value: object) -> str:
    """Оставить только цифры из значения поля формы.

    Args:
        value: Исходное значение поля.

    Returns:
        str: Последовательность цифр без разделителей.
    """
    return "".join(character for character in str(value or "") if character.isdigit())


def _require_valid_email(email: str) -> None:
    """Проверить, что адрес почты не пуст и умещается в ограничение длины.

    Args:
        email: Нормализованный адрес почты.

    Raises:
        FormValidationError: Адрес пуст или слишком длинный.
    """
    if not email or len(email) > EMAIL_MAX_LENGTH:
        raise FormValidationError("Некорректный email")


def _clean_optional(value: object) -> str | None:
    """Вернуть необязательное поле без пробелов или None.

    Args:
        value: Исходное значение поля.

    Returns:
        str | None: Непустое значение либо None.
    """
    cleaned = str(value or "").strip()
    return cleaned or None


def _checkbox(form: dict, name: str) -> bool:
    """Прочитать флажок формы как булево значение.

    Args:
        form: Разобранные данные формы.
        name: Имя флажка.

    Returns:
        bool: True, если флажок отмечен.
    """
    return bool(str(form.get(name) or "").strip())


def map_login_command(form: dict) -> LoginCommand:
    """Проверить форму и собрать команду входа.

    Args:
        form: Разобранные данные формы входа.

    Returns:
        LoginCommand: Команда аутентификации.

    Raises:
        FormValidationError: Почта или пароль не заполнены.
    """
    email = _field_text(form, "email").lower()
    password = str(form.get("password") or "")
    if not email or len(email) > EMAIL_MAX_LENGTH or not password:
        raise FormValidationError("Некорректные данные для входа")
    return LoginCommand(email=email, password=password)


def map_register_command(form: dict) -> RegisterCommand:
    """Проверить форму и собрать команду регистрации.

    Args:
        form: Разобранные данные формы регистрации.

    Returns:
        RegisterCommand: Команда регистрации с темой оформления.

    Raises:
        FormValidationError: Почта, пароль или имя не прошли проверку.
    """
    email = normalize_email(form.get("email"))
    password = str(form.get("password") or "")
    username = _field_text(form, "username")
    _require_valid_email(email)
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise FormValidationError("Пароль должен быть не короче 8 символов")
    if not username or len(username) > USERNAME_MAX_LENGTH:
        raise FormValidationError("Некорректный username")
    return RegisterCommand(
        email=email,
        password=password,
        username=username,
        theme=normalize_theme(form.get("theme")),
    )


def map_verify_email_command(form: dict) -> VerifyEmailCommand:
    """Проверить форму и собрать команду подтверждения почты.

    Args:
        form: Разобранные данные формы подтверждения.

    Returns:
        VerifyEmailCommand: Команда с почтой и кодом из цифр.

    Raises:
        FormValidationError: Почта некорректна или код не состоит из шести цифр.
    """
    email = normalize_email(form.get("email"))
    code = _extract_digits(form.get("code"))
    _require_valid_email(email)
    if len(code) != VERIFICATION_CODE_DIGITS:
        raise FormValidationError("Код подтверждения должен содержать 6 цифр")
    return VerifyEmailCommand(email=email, code=code)


def map_resend_verification_command(form: dict) -> ResendVerificationCommand:
    """Проверить форму и собрать команду повторной отправки кода.

    Args:
        form: Разобранные данные формы повторной отправки.

    Returns:
        ResendVerificationCommand: Команда с нормализованным адресом почты.

    Raises:
        FormValidationError: Адрес почты некорректен.
    """
    email = normalize_email(form.get("email"))
    _require_valid_email(email)
    return ResendVerificationCommand(email=email)


def map_request_password_reset_command(form: dict, *, base_url: str) -> RequestPasswordResetCommand:
    """Проверить форму и собрать команду запроса сброса пароля.

    Args:
        form: Разобранные данные формы запроса сброса.
        base_url: Базовый адрес приложения для ссылки в письме.

    Returns:
        RequestPasswordResetCommand: Команда запроса сброса.

    Raises:
        FormValidationError: Адрес почты некорректен.
    """
    email = normalize_email(form.get("email"))
    _require_valid_email(email)
    return RequestPasswordResetCommand(email=email, base_url=base_url)


def map_confirm_password_reset_command(form: dict) -> ConfirmPasswordResetCommand:
    """Проверить форму и собрать команду подтверждения сброса пароля.

    Args:
        form: Разобранные данные формы с новым паролем и токеном.

    Returns:
        ConfirmPasswordResetCommand: Команда подтверждения сброса.

    Raises:
        FormValidationError: Пароли не совпадают или пароль слишком короткий.
    """
    token = _field_text(form, "token")
    password = str(form.get("password") or "")
    password_repeat = str(form.get("password_repeat") or "")
    if password != password_repeat:
        raise FormValidationError("Пароли не совпадают")
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise FormValidationError("Пароль должен быть не короче 8 символов")
    return ConfirmPasswordResetCommand(token=token, password=password)


def map_update_profile_command(
    form: dict,
    *,
    user_id: int,
    uploaded_avatar_url: str | None = None,
) -> UpdateProfileCommand:
    """Проверить форму и собрать команду правки профиля.

    Args:
        form: Разобранные данные формы профиля.
        user_id: Идентификатор вошедшего пользователя.
        uploaded_avatar_url: Адрес аватара, уже сохранённый хранилищем; перекрывает
            поле формы, если передан.

    Returns:
        UpdateProfileCommand: Команда обновления профиля.

    Raises:
        FormValidationError: Статус длиннее допустимого.
    """
    username = _field_text(form, "username")
    avatar_value = form.get("avatar_url")
    form_avatar_url = None if hasattr(avatar_value, "filename") else _clean_optional(avatar_value)
    avatar_url = uploaded_avatar_url or form_avatar_url
    status = _field_text(form, "status")
    if len(status) > STATUS_MAX_LENGTH:
        raise FormValidationError(f"Статус не может быть длиннее {STATUS_MAX_LENGTH} символов")
    return UpdateProfileCommand(
        user_id=user_id,
        username=username,
        avatar_url=avatar_url,
        status=status or None,
        show_watch_activity=_checkbox(form, "show_watch_activity"),
        show_recent_episodes=_checkbox(form, "show_recent_episodes"),
    )

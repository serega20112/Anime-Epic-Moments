from __future__ import annotations

import pytest
from fastapi import Request

from backend.application.policies import ProxyTrustPolicy
from backend.presentation.dependencies.client_ip import client_ip

TRUSTED = ProxyTrustPolicy(trusted_proxies=("10.0.0.100",))
TRUSTED_CIDR = ProxyTrustPolicy(trusted_proxies=("10.0.0.0/24",))
BROKEN_CONFIG = ProxyTrustPolicy(trusted_proxies=("не-ip", ""))


def _build_request(peer: str | None, forwarded_for: str | None = None) -> Request:
    """Собрать минимальный HTTP-запрос с заданным сокет-пиром.

    Args:
        peer: Адрес сокет-пира либо None.
        forwarded_for: Значение заголовка X-Forwarded-For, если нужно.

    Returns:
        Request: Объект запроса для вызова client_ip.
    """
    headers = []
    if forwarded_for is not None:
        headers.append((b"x-forwarded-for", forwarded_for.encode("latin-1")))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": headers,
        "client": (peer, 12345) if peer else None,
        "server": ("testserver", 80),
        "scheme": "http",
        "root_path": "",
    }
    return Request(scope)


@pytest.mark.unit
class TestClientIp:
    """Юнит-тесты определения IP клиента (задача S3.1)."""

    async def test_ignores_forwarded_for_from_untrusted_peer(self):
        """Что тестируем: запрос с чужого адреса при доверенном прокси 10.0.0.100.
        Что передаём: пир 203.0.113.7 и поддельный X-Forwarded-For.
        Что ожидаем: адрес пира — заголовок игнорируется, иначе ключ
        ограничения частоты можно вращать подменой заголовка.
        """
        request = _build_request(peer="203.0.113.7", forwarded_for="10.0.0.1, 10.0.0.2")

        assert await client_ip(request, TRUSTED) == "203.0.113.7"

    async def test_honors_forwarded_for_from_trusted_proxy(self):
        """Что тестируем: запрос от доверенного прокси.
        Что передаём: пир 10.0.0.100 и список адресов в X-Forwarded-For.
        Что ожидаем: первый адрес из списка — за ним стоит реальный клиент.
        """
        request = _build_request(peer="10.0.0.100", forwarded_for="10.0.0.1, 10.0.0.2")

        assert await client_ip(request, TRUSTED) == "10.0.0.1"

    async def test_accepts_cidr_entries_in_trusted_list(self):
        """Что тестируем: CIDR-запись в списке доверенных прокси.
        Что передаём: пир 10.0.0.57 и сеть 10.0.0.0/24.
        Что ожидаем: первый адрес из X-Forwarded-For.
        """
        request = _build_request(peer="10.0.0.57", forwarded_for="203.0.113.4")

        assert await client_ip(request, TRUSTED_CIDR) == "203.0.113.4"

    async def test_malformed_config_falls_back_to_socket_peer(self):
        """Что тестируем: некорректные значения в конфиге прокси.
        Что передаём: список из мусорной строки и пустой строки.
        Что ожидаем: адрес сокет-пира — недоверенным считается всё, что нельзя
        разобрать, вместо падения разбора.
        """
        request = _build_request(peer="198.51.100.9", forwarded_for="10.0.0.1")

        assert await client_ip(request, BROKEN_CONFIG) == "198.51.100.9"

    async def test_without_forwarded_header_returns_peer(self):
        """Что тестируем: запрос от доверенного прокси без X-Forwarded-For.
        Что передаём: пир 198.51.100.9 и пустой заголовок.
        Что ожидаем: адрес пира.
        """
        request = _build_request(peer="198.51.100.9")

        assert await client_ip(request, TRUSTED) == "198.51.100.9"

    async def test_missing_client_information_returns_unknown(self):
        """Что тестируем: запрос без данных о сокете.
        Что передаём: scope без client.
        Что ожидаем: ``unknown`` вместо исключения.
        """
        request = _build_request(peer=None)

        assert await client_ip(request, TRUSTED) == "unknown"

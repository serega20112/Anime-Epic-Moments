"""Определение IP клиента с учётом доверенных прокси.

Заголовок ``X-Forwarded-For`` подделывается клиентом, поэтому он принимается
только когда непосредственный сокет-пир запроса входит в ``TRUSTED_PROXIES``.
В остальных случаях берётся адрес сокета — иначе атакующий мог бы вращать ключ
ограничения частоты поддельным заголовком. Хелпер относится к presentation, так
как оперирует HTTP-запросом.
"""

from __future__ import annotations

from ipaddress import ip_address, ip_network

from fastapi import Request

from backend.application.policies import ProxyTrustPolicy
from backend.presentation.dependencies.container import resolve

FORWARDED_FOR_HEADER = "X-Forwarded-For"
UNKNOWN_IP = "unknown"


def _is_trusted_proxy(peer: str | None, trusted: tuple[str, ...] | list[str]) -> bool:
    """Проверить, входит ли адрес пира в список доверенных прокси.

    Принимаются и одиночные адреса, и CIDR-сети. Некорректные значения в
    конфиге считаются недоверенными, чтобы вернуться к более безопасному пути
    через сокет-пир.

    Args:
        peer: Непосредственный адрес сокета запроса.
        trusted: Настроенный список доверенных прокси.

    Returns:
        bool: True, если пир является доверенным прокси.
    """
    if not peer or not trusted:
        return False
    try:
        peer_ip = ip_address(peer)
    except ValueError:
        return False
    for value in trusted:
        try:
            if "/" in value:
                if peer_ip in ip_network(value, strict=False):
                    return True
            elif ip_address(value) == peer_ip:
                return True
        except ValueError:
            continue
    return False


async def client_ip(request: Request, policy: ProxyTrustPolicy | None = None) -> str:
    """Вернуть IP клиента, доверяя ``X-Forwarded-For`` только прокси из конфига.

    Args:
        request: Текущий HTTP-запрос.
        policy: Список доверенных прокси; если не передан, берётся из
            контейнера зависимостей по запросу.

    Returns:
        str: Определённый адрес клиента либо ``unknown`` без данных сокета.

    Raises:
        ContainerUnavailableError: Политика не передана и контейнер
            недоступен для этого запроса.
    """
    trusted_proxies = (policy or await resolve(request, ProxyTrustPolicy)).trusted_proxies
    peer = request.client.host.strip() if request.client and request.client.host else None
    if peer and _is_trusted_proxy(peer, trusted_proxies):
        forwarded_for = request.headers.get(FORWARDED_FOR_HEADER, "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip() or peer
    return peer or UNKNOWN_IP

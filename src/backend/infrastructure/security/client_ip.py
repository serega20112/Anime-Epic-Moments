"""Client IP resolution with trusted-proxy validation.

``X-Forwarded-For`` is spoofable; it is honored only when the direct socket
peer is listed in ``Settings.trusted_proxies``.
"""

from __future__ import annotations

from ipaddress import ip_address, ip_network

from fastapi import Request

from backend.config import Settings


def _is_trusted_proxy(peer: str | None, trusted: list[str]) -> bool:
    """Return True when peer address is inside one of the trusted proxies.

    Both plain IPs and CIDR networks are accepted. Malformed values in the
    config are treated as not-trusted so the safer socket-path is used.
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


async def client_ip(request: Request) -> str:
    """Return the client IP, honoring X-Forwarded-For only when the direct peer is a trusted proxy.

    X-Forwarded-For is spoofable; it is ignored unless the socket peer is in
    Settings.trusted_proxies. When not trusted the socket peer is used, so an
    attacker cannot rotate the rate-limit key by forging the header.

    Args:
        request: Incoming HTTP request.

    Returns:
        str: Resolved client IP address.
    """
    peer = request.client.host.strip() if request.client and request.client.host else None
    if peer and _is_trusted_proxy(peer, Settings.trusted_proxies):
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip() or peer
    return peer or "unknown"

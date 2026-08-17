from __future__ import annotations

from backend.infrastructure.security.rate_limit_keys import (
    support_ticket_subject,
    watch_anime_subject,
    watch_user_subject,
)


class TestSupportTicketSubject:
    async def test_authenticated_user(self):
        assert await support_ticket_subject(ip_address="1.2.3.4", user_id=9) == "1.2.3.4::user::9"

    async def test_guest(self):
        assert await support_ticket_subject(ip_address="1.2.3.4", user_id=None) == "1.2.3.4::guest"


class TestWatchAnimeSubject:
    async def test_with_anime(self):
        assert await watch_anime_subject(ip_address="1.2.3.4", anime_id=7) == "1.2.3.4::7"

    async def test_without_anime(self):
        assert await watch_anime_subject(ip_address="1.2.3.4", anime_id=None) == "1.2.3.4::unknown"


class TestWatchUserSubject:
    async def test_authenticated_user(self):
        assert await watch_user_subject(ip_address="1.2.3.4", user_id=5) == "1.2.3.4::5"

    async def test_guest(self):
        assert await watch_user_subject(ip_address="1.2.3.4", user_id=None) == "1.2.3.4::guest"

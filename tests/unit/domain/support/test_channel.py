from __future__ import annotations

from backend.domain.entities.support.channel import (
    DEFAULT_SUPPORT_CHANNEL,
    SUPPORT_CHANNELS,
    is_support_channel,
    normalize_support_channel,
)


class TestSupportChannelConstants:
    async def test_supported_channels(self):
        assert SUPPORT_CHANNELS == frozenset({"telegram", "email"})

    async def test_default_channel(self):
        assert DEFAULT_SUPPORT_CHANNEL == "telegram"


class TestNormalizeSupportChannel:
    async def test_known_channels_are_normalized(self):
        assert normalize_support_channel("TELEGRAM") == "telegram"
        assert normalize_support_channel(" Email ") == "email"

    async def test_unknown_falls_back_to_default(self):
        assert normalize_support_channel("sms") == "telegram"

    async def test_none_falls_back_to_default(self):
        assert normalize_support_channel(None) == "telegram"

    async def test_custom_default(self):
        assert normalize_support_channel("sms", default="email") == "email"


class TestIsSupportChannel:
    async def test_known_channels(self):
        assert is_support_channel("telegram") is True
        assert is_support_channel("EMAIL") is True

    async def test_unknown_and_none(self):
        assert is_support_channel("sms") is False
        assert is_support_channel(None) is False

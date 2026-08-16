from __future__ import annotations

from backend.domain.support.channel import (
    DEFAULT_SUPPORT_CHANNEL,
    SUPPORT_CHANNELS,
    is_support_channel,
    normalize_support_channel,
)


class TestSupportChannelConstants:
    def test_supported_channels(self):
        assert SUPPORT_CHANNELS == frozenset({"telegram", "email"})

    def test_default_channel(self):
        assert DEFAULT_SUPPORT_CHANNEL == "telegram"


class TestNormalizeSupportChannel:
    def test_known_channels_are_normalized(self):
        assert normalize_support_channel("TELEGRAM") == "telegram"
        assert normalize_support_channel(" Email ") == "email"

    def test_unknown_falls_back_to_default(self):
        assert normalize_support_channel("sms") == "telegram"

    def test_none_falls_back_to_default(self):
        assert normalize_support_channel(None) == "telegram"

    def test_custom_default(self):
        assert normalize_support_channel("sms", default="email") == "email"


class TestIsSupportChannel:
    def test_known_channels(self):
        assert is_support_channel("telegram") is True
        assert is_support_channel("EMAIL") is True

    def test_unknown_and_none(self):
        assert is_support_channel("sms") is False
        assert is_support_channel(None) is False

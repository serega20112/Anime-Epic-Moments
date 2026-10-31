from __future__ import annotations

import pytest

from backend.application.dto import (
    AskAiRecommendationsCommand,
    CreateSupportTicketCommand,
)
from backend.domain.value_objects.reaction.reaction_summary import (
    EpisodeReactionCount,
    EpisodeReactionSummary,
)
from backend.domain.value_objects.reaction.reaction_type import (
    EpisodeReactionEmoji,
    EpisodeReactionType,
)
from backend.presentation.api.requests.reaction_mapper import (
    map_episode_reactions_response,
    map_set_episode_reaction_command,
)
from backend.presentation.api.requests.reaction_requests import SetEpisodeReactionRequest
from backend.presentation.api.requests.recommendation_mapper import (
    ASK_LIMIT_DEFAULT,
    ASK_LIMIT_MAX,
    ASK_LIMIT_MIN,
    _clamp_limit,
    map_ask_ai_command,
)
from backend.presentation.api.requests.recommendation_requests import AskAiRecommendationsRequest
from backend.presentation.api.requests.support_form_builder import (
    build_default_support_form,
    build_support_form_data,
)
from backend.presentation.api.requests.support_mapper import map_create_support_ticket_command


@pytest.mark.unit
class TestRecommendationMapper:
    """Юнит-тесты построения команды запроса AI-рекомендаций."""

    def test_trims_query_and_uses_default_limit(self):
        """Что тестируем: нормализацию тела запроса к ИИ.
        Что передаём: тело с пробелами вокруг запроса и без лимита.
        Что ожидаем: обрезанный запрос и лимит по умолчанию.
        """
        command = map_ask_ai_command(
            AskAiRecommendationsRequest(query="  аниме про космос  "), user_id=5
        )

        assert command == AskAiRecommendationsCommand(
            user_id=5, query="аниме про космос", limit=ASK_LIMIT_DEFAULT
        )

    @pytest.mark.parametrize(
        ("requested", "expected"),
        [
            (None, ASK_LIMIT_DEFAULT),
            (0, ASK_LIMIT_MIN),
            (3, 3),
            (99, ASK_LIMIT_MAX),
        ],
    )
    def test_clamps_limit_into_allowed_range(self, requested, expected):
        """Что тестируем: защитный кламп размера выдачи.
        Что передаём: отсутствующий, слишком маленький, корректный и большой лимиты.
        Что ожидаем: значение внутри диапазона от одного до десяти.
        """
        assert _clamp_limit(requested) == expected


@pytest.mark.unit
class TestReactionMapper:
    """Юнит-тесты построения команд и ответов маршрутов реакций."""

    def test_command_keeps_liked_flag_and_trims_reaction(self):
        """Что тестируем: сборку команды реакции из проверенного тела.
        Что передаём: тело с типом реакции в пробелах и liked=False.
        Что ожидаем: идентификаторы из пути, обрезанный тип и флаг снятия.
        """
        command = map_set_episode_reaction_command(
            SetEpisodeReactionRequest(episode=3, reaction=" fire ", timestamp=12.5, liked=False),
            user_id=5,
            anime_id=19,
        )

        assert command.user_id == 5
        assert command.anime_id == 19
        assert command.episode == 3
        assert command.reaction_type == "fire"
        assert command.timestamp == 12.5
        assert command.liked is False

    def test_response_exposes_emoji_and_user_reaction(self):
        """Что тестируем: сборку JSON-сводки реакций.
        Что передаём: сводку с одним счётчиком и реакцией зрителя.
        Что ожидаем: эмодзи типа, число и значение реакции пользователя.
        """
        response = map_episode_reactions_response(
            EpisodeReactionSummary(
                counts=[EpisodeReactionCount(reaction_type=EpisodeReactionType.FIRE, count=4)],
                user_reaction=EpisodeReactionType.FIRE,
            )
        )

        assert response.counts[0].reaction_type == "fire"
        assert response.counts[0].emoji == EpisodeReactionEmoji.FIRE.value
        assert response.counts[0].count == 4
        assert response.user_reaction == "fire"

    def test_empty_summary_response_has_no_user_reaction(self):
        """Что тестируем: сводку без реакций.
        Что передаём: пустую доменную сводку.
        Что ожидаем: пустой список счётчиков и None у реакции зрителя.
        """
        response = map_episode_reactions_response(EpisodeReactionSummary.empty())

        assert response.counts == []
        assert response.user_reaction is None


@pytest.mark.unit
class TestSupportMapper:
    """Юнит-тесты сборки команды и данных формы обращения в поддержку."""

    def test_session_user_credentials_win_over_form(self):
        """Что тестируем: приоритет данных сессии над полями формы для авторизованного.
        Что передаём: форму с чужими почтой и именем плюс пользователя сессии.
        Что ожидаем: команда с почтой и именем из сессии.
        """
        command = map_create_support_ticket_command(
            {
                "email": "spoofed@example.com",
                "username": "spoofed",
                "subject": " Тема ",
                "message": "M",
            },
            user_id=5,
            user_email="Real@Example.com ",
            user_username="  Иван   Петров ",
        )

        assert command.user_id == 5
        assert command.email == "real@example.com"
        assert command.username == "Иван Петров"
        assert command.subject == "Тема"

    def test_guest_credentials_come_from_form(self):
        """Что тестируем: сборку команды гостя из полей формы.
        Что передаём: форму без идентификатора пользователя сессии.
        Что ожидаем: user_id=None, канал по умолчанию и None у пустого адреса страницы.
        """
        command = map_create_support_ticket_command(
            {
                "email": "guest@example.com",
                "username": "guest",
                "subject": "Сломан поиск",
                "message": "Поиск пустой",
                "channel": "email",
                "page_url": "  /anime/search  ",
            },
            user_id=None,
        )

        assert command.user_id is None
        assert command.email == "guest@example.com"
        assert command.channel == "email"
        assert command.page_url == "/anime/search"

    def test_page_url_is_truncated_to_limit(self):
        """Что тестируем: обрезку слишком длинного адреса страницы.
        Что передаём: адрес длиннее допустимого лимита.
        Что ожидаем: адрес ровно лимита по длине.
        """
        command = map_create_support_ticket_command(
            {"page_url": "/watch/1?" + "a" * 600},
            user_id=None,
        )

        assert command.page_url is not None
        assert len(command.page_url) == 500

    def test_form_data_prefers_session_credentials(self):
        """Что тестируем: повторный показ формы после отказа.
        Что передаём: команду и пользователя сессии.
        Что ожидаем: почта и имя из сессии, поля команды сохранены.
        """
        form_data = build_support_form_data(
            command=CreateSupportTicketCommand(
                user_id=5,
                email="from-form@example.com",
                username="from-form",
                subject="Тема",
                message="Сообщение",
                channel="email",
                page_url="/watch/1",
            ),
            user_email="Session@Example.com",
            user_username="Андрей",
        )

        assert form_data["email"] == "session@example.com"
        assert form_data["username"] == "Андрей"
        assert form_data["subject"] == "Тема"
        assert form_data["channel"] == "email"
        assert form_data["page_url"] == "/watch/1"

    def test_default_form_falls_back_to_empty_credentials(self):
        """Что тестируем: предзаполнение формы для гостя.
        Что передаём: пустые почту и имя, неизвестный канал.
        Что ожидаем: пустые поля, канал по умолчанию и пустой адрес страницы.
        """
        form_data = build_default_support_form(channel_param="discord", page_param=None)

        assert form_data["email"] == ""
        assert form_data["username"] == ""
        assert form_data["channel"] == "telegram"
        assert form_data["page_url"] == ""

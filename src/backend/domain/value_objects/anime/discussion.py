class AnimeDiscussionComment:
    """Комментарий в обсуждении аниме."""

    def __init__(
        self,
        id: int,
        anime_id: int,
        user_id: int,
        username: str,
        content: str,
        likes_count: int,
        created_at: str,
        is_liked: bool = False,
    ):
        self.id = id
        self.anime_id = anime_id
        self.user_id = user_id
        self.username = username
        self.content = content
        self.likes_count = likes_count
        self.created_at = created_at
        self.is_liked = is_liked


class AnimeDiscussionBoard:
    """Доска обсуждения аниме с сортировкой и счетчиками."""

    def __init__(
        self,
        anime_id: int,
        items: list[AnimeDiscussionComment],
        selected_sort: str,
        total_comments: int,
    ):
        self.anime_id = anime_id
        self.items = items
        self.selected_sort = selected_sort
        self.total_comments = total_comments

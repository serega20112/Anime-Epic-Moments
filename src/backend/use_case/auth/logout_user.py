"""
Use case для выхода пользователя (logout)
"""


class LogoutUserUseCase:
    """
    Завершает сессию пользователя
    """

    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def execute(self, user_id: int):
        """
        Логаут пользователя: можно удалить токен из БД или кэша
        """
        await self.user_repository.clear_user_session(user_id)
        return True

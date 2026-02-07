from uuid import UUID

from application.usecases.base import UseCase
from domain.interfaces.repositories import IUserRepository


class DeleteUserUseCase(UseCase):
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: UUID):
        return self.user_repo.delete(user_id)

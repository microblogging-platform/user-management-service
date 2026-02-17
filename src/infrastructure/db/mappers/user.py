from domain.entities import User
from infrastructure.db.models import UserModel

from .base import BaseMapper


class UserMapper(BaseMapper[User, UserModel]):
    def __init__(self) -> None:
        super().__init__(User, UserModel)


user_mapper = UserMapper()

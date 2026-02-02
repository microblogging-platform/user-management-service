from domain.entities import User
from domain.enums import Role
from domain.interfaces.repositories import IUserRepository
from domain.interfaces.security import IPasswordHasher
from application.dto.user import RegisterUserCommand, UserDTO
from domain.exceptions import UserAlreadyExistsError


class RegisterUserUseCase:
    def __init__(
            self,
            user_repo: IUserRepository,
            password_hasher: IPasswordHasher,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher

    async def execute(self, command: RegisterUserCommand) -> UserDTO:

        if await self.user_repo.exists_by_username(command.username):
            raise UserAlreadyExistsError(f"Username {command.username} already exists")

        if await self.user_repo.exists_by_email(command.email):
            raise UserAlreadyExistsError(f"Email {command.email} already exists")

        password_hash = self.password_hasher.hash(command.password)

        new_user = User(
            name=command.name,
            surname=command.surname,
            username=command.username,
            password_hash=password_hash,
            email=command.email,
            phone_number=command.phone_number,
            role=Role.USER,
            image_s3_path="",
            is_blocked=False,
            group_id=None
        )

        created_user = await self.user_repo.create(new_user)

        return UserDTO.model_validate(created_user)
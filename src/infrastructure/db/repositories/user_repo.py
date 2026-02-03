from uuid import UUID
from pydantic import EmailStr
from domain.entities import User
from sqlalchemy import or_, select
from infrastructure.db.models import UserModel
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.db.mappers import user_mapper
from domain.interfaces.repositories import IUserRepository


class SqlAlchemyUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = user_mapper

    async def create(self, user: User) -> User:
        user_model = self._mapper.to_model(user)
        self._session.add(user_model)
        await self._session.flush()
        await self._session.refresh(user_model)
        return self._mapper.to_domain(user_model)

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()
        return self._mapper.to_domain(user_model) if user_model else None

    async def get_by_login_identifier(self, identifier: str) -> User | None:
        stmt = select(UserModel).where(
            or_(
                UserModel.email == identifier,
                UserModel.username == identifier,
                UserModel.phone_number == identifier,
            )
        )
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()

        return self._mapper.to_domain(user_model) if user_model else None

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()
        return self._mapper.to_domain(user_model) if user_model else None

    async def get_by_email(self, email: EmailStr) -> User | None:
        stmt = select(UserModel).where(UserModel.email == str(email))
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()
        return self._mapper.to_domain(user_model) if user_model else None

    async def get_by_group_id(self, group_id: UUID) -> list[User]:
        stmt = select(UserModel).where(UserModel.group_id == group_id)
        result = await self._session.execute(stmt)
        user_models = result.scalars().all()
        return [self._mapper.to_domain(model) for model in user_models]

    async def update(self, user: User) -> User:
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()

        if not user_model:
            raise ValueError(f"User with id {user.id} not found")

        user_model.name = user.name
        user_model.surname = user.surname
        user_model.username = user.username
        user_model.phone_number = str(user.phone_number)
        user_model.email = str(user.email)
        user_model.role = user.role
        user_model.image_s3_path = user.image_s3_path
        user_model.is_blocked = user.is_blocked
        user_model.group_id = user.group_id

        await self._session.flush()
        await self._session.refresh(user_model)
        return self._mapper.to_domain(user_model)

    async def delete(self, user_id: UUID) -> None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()

        if user_model:
            await self._session.delete(user_model)
            await self._session.flush()

    async def exists_by_username(self, username: str) -> bool:
        stmt = select(UserModel.id).where(UserModel.username == username).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_email(self, email: EmailStr) -> bool:
        stmt = select(UserModel.id).where(UserModel.email == str(email)).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

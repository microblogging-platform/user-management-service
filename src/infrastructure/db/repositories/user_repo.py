from datetime import datetime
from uuid import UUID
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber

from domain.entities import User
from sqlalchemy import or_, select, asc, desc, func
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

    async def get_by_login_identifier(self, identifier: str | EmailStr | PhoneNumber) -> User | None:
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

    # noinspection PyTypeChecker
    async def update(self, user: User) -> User:
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one()

        user_model.name = user.name
        user_model.surname = user.surname
        user_model.username = user.username
        user_model.email = str(user.email)
        user_model.phone_number = user.phone_number
        user_model.modified_at = user.modified_at
        user_model.image_s3_path = user.image_s3_path

        await self._session.flush()

        return user_mapper.to_domain(user_model)

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

    async def get_all(
            self,
            limit: int,
            offset: int,
            filter_by_name: str | None = None,
            sort_by: str | None = None,
            order_by: str = "asc",
            group_id: UUID | None = None
    ) -> tuple[list[User], int]:

        query = select(UserModel) if group_id is None else select(UserModel).where(UserModel.group_id == group_id)

        if filter_by_name:
            search = f"%{filter_by_name}%"
            query = query.where(
                or_(
                    UserModel.name.ilike(search),
                    UserModel.surname.ilike(search)
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._session.execute(count_query)
        total = total_result.scalar_one()

        column = getattr(UserModel, sort_by) if sort_by and hasattr(UserModel, sort_by) else UserModel.created_at
        query = query.order_by(desc(column)) if order_by == "desc" else query.order_by(asc(column))

        query = query.limit(limit).offset(offset)

        result = await self._session.execute(query)
        users = result.scalars().all()

        return [user_mapper.to_domain(user) for user in users], total

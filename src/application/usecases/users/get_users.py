import math

from application.dto.user import GetUsersQuery, UsersListResponse, UserDTO
from application.usecases.base import UseCase
from domain.entities import User
from domain.enums import Role
from domain.exceptions import ForbiddenError
from domain.interfaces.repositories import IUserRepository


class GetUsersUseCase(UseCase):
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, query: GetUsersQuery, requester: User) -> UsersListResponse:
        target_group_id = None

        if requester.role == Role.ADMIN:
            pass

        elif requester.role == Role.MODERATOR:
            if not requester.group_id:
                return self._empty_response(query)

            target_group_id = requester.group_id
        else:
            raise ForbiddenError("You don't have permission to list users")

        offset = (query.page - 1) * query.limit

        users, total = await self.user_repo.get_all(
            limit=query.limit,
            offset=offset,
            filter_by_name=query.filter_by_name,
            sort_by=query.sort_by,
            order_by=query.order_by,
            group_id=target_group_id
        )

        pages = math.ceil(total / query.limit) if query.limit > 0 else 0

        return UsersListResponse(
            items=[UserDTO.model_validate(u) for u in users],
            total=total,
            page=query.page,
            limit=query.limit,
            pages=pages
        )

    def _empty_response(self, query: GetUsersQuery) -> UsersListResponse:
        return UsersListResponse(items=[], total=0, page=query.page, limit=query.limit, pages=0)
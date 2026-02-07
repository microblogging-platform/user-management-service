import math

from application.dto.user import GetUsersQuery, UsersListResponse, UserDTO
from application.usecases.base import UseCase
from domain.entities import User
from domain.enums import Role
from domain.exceptions import ForbiddenError
from domain.interfaces.repositories import IUserRepository
from domain.interfaces.services.storage import IStorageService


class GetUsersUseCase(UseCase):
    def __init__(self, user_repo: IUserRepository, storage_service: IStorageService):
        self.user_repo = user_repo
        self.storage_service = storage_service

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
            group_id=target_group_id,
        )

        pages = math.ceil(total / query.limit) if query.limit > 0 else 0

        user_dtos = []
        for user in users:
            dto = UserDTO.model_validate(user)

            if user.image_s3_path:
                dto.image_s3_path = await self.storage_service.generate_presigned_get_url(user.image_s3_path)

            user_dtos.append(dto)

        return UsersListResponse(items=user_dtos, total=total, page=query.page, limit=query.limit, pages=pages)

    def _empty_response(self, query: GetUsersQuery) -> UsersListResponse:
        return UsersListResponse(items=[], total=0, page=query.page, limit=query.limit, pages=0)

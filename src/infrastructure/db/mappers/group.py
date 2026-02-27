from domain.entities import Group
from infrastructure.db.models import GroupModel

from .base import BaseMapper


class GroupMapper(BaseMapper[Group, GroupModel]):
    def __init__(self) -> None:
        super().__init__(Group, GroupModel)


group_mapper = GroupMapper()

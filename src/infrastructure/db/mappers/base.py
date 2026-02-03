from typing import Generic, Type, TypeVar

from infrastructure.db import Base
from pydantic import BaseModel

DomainT = TypeVar("DomainT", bound=BaseModel)
ModelT = TypeVar("ModelT", bound=Base)


class BaseMapper(Generic[DomainT, ModelT]):

    def __init__(self, domain_type: Type[DomainT], model_type: Type[ModelT]) -> None:
        self._domain_type = domain_type
        self._model_type = model_type

    def to_domain(self, model: ModelT) -> DomainT:
        return self._domain_type.model_validate(model, from_attributes=True)

    def to_model(self, entity: DomainT) -> ModelT:
        data = entity.model_dump()
        return self._model_type(**data)

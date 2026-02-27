from abc import ABC, abstractmethod
from typing import Any, Dict


class IMessageBroker(ABC):
    @abstractmethod
    async def publish(self, queue_name: str, message: Dict[str, Any]) -> None:
        pass

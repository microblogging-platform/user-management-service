from datetime import datetime, timezone

from application.usecases.base import UseCase
from domain.interfaces.repositories import IUserRepository
from domain.interfaces.security import ITokenService
from domain.interfaces.services.message_broker import IMessageBroker
from infrastructure.config import settings


class RequestPasswordResetUseCase(UseCase):
    def __init__(self, user_repo: IUserRepository, token_service: ITokenService, message_broker: IMessageBroker):
        self.user_repo = user_repo
        self.token_service = token_service
        self.message_broker = message_broker
        self.queue_name = "reset-password-stream"

    async def execute(self, login: str) -> None:
        user = await self.user_repo.get_by_login_identifier(login)

        if not user:
            return

        token = self.token_service.create_reset_token(data={"sub": str(user.id)})

        reset_link = f"{settings.frontend_url}/reset-password?token={token}"

        event_message = {
            "event_type": "password_reset_requested",
            "payload": {
                "recipient_email": user.email,
                "username": user.username,
                "reset_link": reset_link,
            },
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        }

        await self.message_broker.publish(queue_name=self.queue_name, message=event_message)

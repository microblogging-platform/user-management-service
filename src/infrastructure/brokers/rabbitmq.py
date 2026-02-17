import json
import logging
from typing import Any, Dict

from aio_pika import DeliveryMode, Message, RobustConnection

from domain.interfaces.services.message_broker import IMessageBroker


class RabbitMQService(IMessageBroker):
    def __init__(self, connection: RobustConnection):
        self.connection = connection

    async def publish(self, queue_name: str, message: Dict[str, Any]) -> None:
        try:
            async with self.connection.channel() as channel:
                await channel.declare_queue(queue_name, durable=True)

                await channel.default_exchange.publish(
                    Message(
                        body=json.dumps(message).encode(),
                        delivery_mode=DeliveryMode.PERSISTENT,
                        content_type="application/json",
                    ),
                    routing_key=queue_name,
                )
        except Exception as e:
            logging.error(f"Failed to publish message to RabbitMQ: {e}", exc_info=True)
            raise

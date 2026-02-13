import logging

import aio_pika

from infrastructure.config import settings

_connection: aio_pika.RobustConnection | None = None


async def get_rabbitmq_connection() -> aio_pika.RobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return _connection


async def init_rabbitmq() -> None:
    global _connection
    logging.info("Connecting to RabbitMQ...")
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    logging.info("Connected to RabbitMQ.")


async def close_rabbitmq() -> None:
    global _connection
    if _connection:
        await _connection.close()
        logging.info("RabbitMQ connection closed.")

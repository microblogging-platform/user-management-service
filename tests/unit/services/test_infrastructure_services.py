import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from infrastructure.brokers import connection
from infrastructure.brokers.rabbitmq import RabbitMQService
from infrastructure.db.redis import get_redis_client
from infrastructure.db.session import get_db_session
from infrastructure.security.redis_blacklist import RedisTokenBlacklistService as SecurityRedisBlacklist
from infrastructure.services.redis_blacklist import RedisTokenBlacklistService as ServicesRedisBlacklist
from infrastructure.services.s3_service import S3Service


def run(coro):
    return asyncio.run(coro)


def test_rabbitmq_service_publish_success():
    channel = AsyncMock()
    channel.default_exchange.publish = AsyncMock()
    channel.declare_queue = AsyncMock()
    connection_obj = Mock()
    channel_context = AsyncMock()
    channel_context.__aenter__.return_value = channel
    channel_context.__aexit__.return_value = False
    connection_obj.channel.return_value = channel_context
    service = RabbitMQService(connection_obj)

    run(service.publish("events", {"key": "value"}))

    channel.declare_queue.assert_awaited_once_with("events", durable=True)
    channel.default_exchange.publish.assert_awaited_once()


def test_rabbitmq_service_publish_failure_raises():
    connection_obj = Mock()
    channel_context = AsyncMock()
    channel_context.__aenter__.side_effect = RuntimeError("channel fail")
    connection_obj.channel.return_value = channel_context
    service = RabbitMQService(connection_obj)

    with pytest.raises(RuntimeError):
        run(service.publish("events", {"key": "value"}))


def test_connection_lifecycle(monkeypatch):
    conn = Mock()
    conn.is_closed = False
    conn.close = AsyncMock()
    monkeypatch.setattr(connection, "_connection", None)
    monkeypatch.setattr(connection.aio_pika, "connect_robust", AsyncMock(return_value=conn))

    created = run(connection.get_rabbitmq_connection())
    assert created is conn

    run(connection.init_rabbitmq())
    run(connection.close_rabbitmq())
    conn.close.assert_awaited()


def test_redis_blacklist_services():
    redis = AsyncMock()
    redis.exists.return_value = 1

    security_service = SecurityRedisBlacklist(redis)
    services_service = ServicesRedisBlacklist(redis)

    run(security_service.blacklist_token("token-a", 123))
    run(services_service.blacklist_token("token-b", 456))
    assert run(security_service.is_blacklisted("token-a")) is True
    assert run(services_service.is_blacklisted("token-b")) is True


def test_redis_dependency_closes_client(monkeypatch):
    client = AsyncMock()
    monkeypatch.setattr("infrastructure.db.redis.from_url", Mock(return_value=client))
    agen = get_redis_client()

    yielded = run(agen.__anext__())
    assert yielded is client

    with pytest.raises(StopAsyncIteration):
        run(agen.__anext__())
    client.close.assert_awaited_once()


def test_db_session_dependency_handles_exceptions(monkeypatch):
    fake_session = AsyncMock()

    class SessionContext:
        async def __aenter__(self):
            return fake_session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    factory = Mock(return_value=SessionContext())
    monkeypatch.setattr("infrastructure.db.session.async_session_factory", factory)

    agen = get_db_session()
    yielded = run(agen.__anext__())
    assert yielded is fake_session

    with pytest.raises(RuntimeError):
        run(agen.athrow(RuntimeError("boom")))
    fake_session.rollback.assert_awaited_once()
    fake_session.close.assert_awaited_once()


def test_s3_service_presigned_and_delete_behaviors():
    s3 = AsyncMock()
    s3.generate_presigned_url = AsyncMock(return_value="https://signed")
    s3.delete_object = AsyncMock()
    cm = AsyncMock()
    cm.__aenter__.return_value = s3
    cm.__aexit__.return_value = False

    service = S3Service()
    service.session = Mock()
    service.session.client.return_value = cm

    assert run(service.generate_presigned_upload_url("avatars/k.png", "image/png")) == "https://signed"
    assert run(service.generate_presigned_get_url("avatars/k.png")) == "https://signed"
    assert run(service.generate_presigned_get_url("")) is None

    run(service.delete_file("avatars/k.png"))
    s3.delete_object.assert_awaited_once()

import pytest
from unittest.mock import AsyncMock, Mock

from infrastructure.brokers import connection
from infrastructure.brokers.rabbitmq import RabbitMQService
from infrastructure.db.redis import get_redis_client
from infrastructure.db.session import get_db_session
from infrastructure.services.redis_blacklist import RedisTokenBlacklistService
from infrastructure.services.s3_service import S3Service


@pytest.mark.asyncio
async def test_rabbitmq_service_publish_success():
    channel = AsyncMock()
    channel.default_exchange.publish = AsyncMock()
    channel.declare_queue = AsyncMock()

    channel_context = AsyncMock()
    channel_context.__aenter__.return_value = channel
    channel_context.__aexit__.return_value = False

    connection_obj = Mock()
    connection_obj.channel.return_value = channel_context

    service = RabbitMQService(connection_obj)
    await service.publish("events", {"key": "value"})

    channel.declare_queue.assert_awaited_once_with("events", durable=True)
    channel.default_exchange.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_rabbitmq_service_publish_failure_raises():
    connection_obj = Mock()
    channel_context = AsyncMock()
    channel_context.__aenter__.side_effect = RuntimeError("channel fail")
    connection_obj.channel.return_value = channel_context

    service = RabbitMQService(connection_obj)

    with pytest.raises(RuntimeError):
        await service.publish("events", {"key": "value"})


@pytest.mark.asyncio
async def test_connection_lifecycle(monkeypatch):
    conn = Mock()
    conn.is_closed = False
    conn.close = AsyncMock()

    monkeypatch.setattr(connection, "_connection", None)
    monkeypatch.setattr(connection.aio_pika, "connect_robust", AsyncMock(return_value=conn))

    created = await connection.get_rabbitmq_connection()
    assert created is conn

    await connection.init_rabbitmq()
    await connection.close_rabbitmq()

    conn.close.assert_awaited()


@pytest.mark.asyncio
async def test_redis_blacklist_service():
    redis = AsyncMock()
    redis.exists.return_value = 1

    services_service = RedisTokenBlacklistService(redis)

    await services_service.blacklist_token("token-b", 456)

    assert await services_service.is_blacklisted("token-b") is True


@pytest.mark.asyncio
async def test_redis_dependency_closes_client(monkeypatch):
    client = AsyncMock()
    monkeypatch.setattr("infrastructure.db.redis.from_url", Mock(return_value=client))

    agen = get_redis_client()

    yielded = await agen.__anext__()
    assert yielded is client

    with pytest.raises(StopAsyncIteration):
        await agen.__anext__()

    client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_db_session_dependency_handles_exceptions(monkeypatch):
    fake_session = AsyncMock()

    class SessionContext:
        async def __aenter__(self):
            return fake_session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    factory = Mock(return_value=SessionContext())
    monkeypatch.setattr("infrastructure.db.session.async_session_factory", factory)

    agen = get_db_session()

    yielded = await agen.__anext__()
    assert yielded is fake_session

    with pytest.raises(RuntimeError):
        await agen.athrow(RuntimeError("boom"))

    fake_session.rollback.assert_awaited_once()
    fake_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_s3_service_presigned_and_delete_behaviors():
    s3 = AsyncMock()
    s3.generate_presigned_url = AsyncMock(return_value="https://signed")
    s3.delete_object = AsyncMock()

    cm = AsyncMock()
    cm.__aenter__.return_value = s3
    cm.__aexit__.return_value = False

    service = S3Service()
    service.session = Mock()
    service.session.client.return_value = cm

    upload_url = await service.generate_presigned_upload_url("avatars/k.png", "image/png")
    assert upload_url == "https://signed"

    get_url = await service.generate_presigned_get_url("avatars/k.png")
    assert get_url == "https://signed"

    empty_url = await service.generate_presigned_get_url("")
    assert empty_url is None

    await service.delete_file("avatars/k.png")
    s3.delete_object.assert_awaited_once()

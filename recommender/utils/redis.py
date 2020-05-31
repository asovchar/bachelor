import logging

from aiohttp.web_app import Application
from aioredis import create_redis, Redis
from configargparse import Namespace

CENSORED = "***"
DEFAULT_REDIS_URL = "redis://:hackme@localhost:6379/0"

log = logging.getLogger(__name__)


async def setup_redis(app: Application, args: Namespace) -> Redis:
    db_info = args.redis_url.with_password(CENSORED)
    log.info("Connecting to cache: %s", db_info)

    app["redis"] = await create_redis(str(args.redis_url))
    await app["redis"].ping()
    log.info(f"Connected to cache %s", db_info)

    try:
        yield
    finally:
        log.info("Disconnecting from cache %s", db_info)
        app["redis"].close()
        await app["redis"].wait_closed()
        log.info("Disconnected from cache %s", db_info)

import logging
from functools import partial
from types import MappingProxyType
from typing import Mapping

from aiohttp import PAYLOAD_REGISTRY
from aiohttp.web_app import Application
from aiohttp_apispec import setup_aiohttp_apispec, validation_middleware
from configargparse import Namespace

from recommender.api.handlers import HANDLERS
from recommender.api.middleware import error_middleware, handle_validation_error
from recommender.api.payloads import JsonPayload
from recommender.utils.pg import setup_pg
from recommender.utils.redis import setup_redis

log = logging.getLogger(__name__)


def create_app(args: Namespace) -> Application:
    app = Application(middlewares=[error_middleware, validation_middleware])
    app.cleanup_ctx.append(partial(setup_pg, args=args))
    app.cleanup_ctx.append(partial(setup_redis, args=args))

    for handler in HANDLERS:
        log.debug('Registering handler %r as %r', handler, handler.URL_PATH)
        app.router.add_route('*', handler.URL_PATH, handler)

    setup_aiohttp_apispec(app=app, title='Recommender API',
                          error_callback=handle_validation_error)

    PAYLOAD_REGISTRY.register(JsonPayload, (Mapping, MappingProxyType))
    return app

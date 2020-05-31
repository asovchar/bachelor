import json
from decimal import Decimal
from functools import partial, singledispatch
from typing import Any

from aiohttp.payload import JsonPayload as BaseJsonPayload, Payload
from aiohttp.typedefs import JSONEncoder
from asyncpg import Record


@singledispatch
def convert(value):
    raise TypeError(f"Unserializable value: {value!r}")


@convert.register(Record)
def convert_asyncpg_record(value: Record):
    return dict(value)


@convert.register(Decimal)
def convert_decimal(value: Decimal):
    return float(value)


dumps = partial(json.dumps, default=convert, ensure_ascii=False)


class JsonPayload(BaseJsonPayload):
    def __init__(self,
                 value: Any,
                 encoding: str = "utf-8",
                 content_type: str = "application/json",
                 dumps: JSONEncoder = dumps,
                 *args: Any,
                 **kwargs: Any) -> None:
        super().__init__(value, encoding, content_type, dumps, *args, **kwargs)


class AsyncGenJSONListPayload(Payload):
    def __init__(self, value, encoding: str = "utf-8",
                 content_type: str = "application/json",
                 root_object: str = "data",
                 *args, **kwargs):
        self.root_object = root_object
        super().__init__(value, content_type=content_type, encoding=encoding,
                         *args, **kwargs)

    async def write(self, writer):
        # Начало объекта
        await writer.write(
            ('{"%s":[' % self.root_object).encode(self._encoding)
        )

        first = True
        async for row in self._value:
            # Перед первой строчкой запятая не нужнаа
            if not first:
                await writer.write(b",")
            else:
                first = False

            await writer.write(dumps(row).encode(self._encoding))

        # Конец объекта
        await writer.write(b"]}")


__all__ = ("JsonPayload", "AsyncGenJSONListPayload")

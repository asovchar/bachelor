from aiohttp.web_exceptions import HTTPNotFound
from aiohttp.web_urldispatcher import View
from aioredis import Redis
from asyncpgsa import PG
from sqlalchemy import select, exists

from recommender.db.schema import items_table, users_table


class BaseView(View):
    URL_PATH: str

    @property
    def pg(self) -> PG:
        return self.request.app["pg"]

    @property
    def redis(self) -> Redis:
        return self.request.app["redis"]


class BaseItemView(BaseView):
    @property
    def item_id(self):
        return int(self.request.match_info.get("item_id"))

    async def check_item_exists(self):
        query = select([
            exists().where(items_table.c.id == self.item_id)
        ])
        if not await self.pg.fetchval(query):
            raise HTTPNotFound()


class BaseUserView(BaseView):
    @property
    def user_id(self):
        return int(self.request.match_info.get("user_id"))

    async def check_user_exists(self):
        query = select([
            exists().where(users_table.c.id == self.user_id)
        ])
        if not await self.pg.fetchval(query):
            raise HTTPNotFound()

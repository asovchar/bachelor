from aiohttp.web_exceptions import HTTPOk
from aiohttp_apispec import querystring_schema
from sqlalchemy import select, desc

from recommender.api.schema import HistoryQSSchema
from recommender.db.schema import (
    users_table, interactions_table, items_table
)

from .base import BaseUserView


class UserHistoryView(BaseUserView):
    URL_PATH = r"/users/{user_id:\d+}/history"

    @property
    def limit(self):
        return int(self.request["querystring"].get("limit", 10))

    @staticmethod
    async def get_history(conn, user_id, limit):
        query = select([
            items_table.c.id,
        ]).select_from(
            users_table.outerjoin(
                interactions_table,
                users_table.c.id == interactions_table.c.user_id
            ).outerjoin(
                items_table,
                items_table.c.id == interactions_table.c.item_id
            )
        ).where(
            users_table.c.id == user_id
        ).group_by(
            interactions_table.c.id,
            items_table.c.id,
        ).order_by(
            desc(interactions_table.c.id)
        ).limit(limit)
        return await conn.fetch(query)

    @querystring_schema(HistoryQSSchema)
    async def get(self):
        await self.check_user_exists()

        async with self.pg.transaction() as conn:
            history = await self.get_history(conn, self.user_id, self.limit)
        return HTTPOk(body={"data": history})

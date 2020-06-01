from aiohttp.web_exceptions import HTTPAccepted
from recommender.db.schema import interactions_table

from .base import BaseUserView, BaseItemView


class InteractionView(BaseUserView, BaseItemView):
    URL_PATH = r"/users/{user_id:\d+}/interact/{item_id:\d+}"

    @staticmethod
    async def save_interaction(conn, user_id, item_id):
        value = {"user_id": user_id, "item_id": item_id}
        query = interactions_table.insert().values(value)
        await conn.execute(query)

    async def post(self):
        await self.check_user_exists()
        await self.check_item_exists()

        async with self.pg.transaction() as conn:
            await self.save_interaction(conn, self.user_id, self.item_id)

        return HTTPAccepted()

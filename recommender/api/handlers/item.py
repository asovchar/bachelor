from aiohttp.web_exceptions import HTTPOk, HTTPAccepted, HTTPNoContent
from aiohttp_apispec import request_schema
from sqlalchemy import func, select

from recommender.api.schema import ItemSchema
from recommender.db.schema import (
    items_table, item_features_table, item_description_table
)

from .base import BaseItemView


class ItemView(BaseItemView):
    URL_PATH = r"/items/{item_id:\d+}"

    @staticmethod
    async def get_item(conn, item_id):
        query = select([
            items_table.c.id,
            func.vec_sum(
                item_features_table.c.embedding
            ).label("embedding"),
            func.array_remove(
                func.array_agg(item_features_table.c.id),
                None
            ).label("feature_ids")
        ]).select_from(
            items_table.outerjoin(
                item_description_table,
                items_table.c.id == item_description_table.c.item_id
            ).outerjoin(
                item_features_table,
                item_features_table.c.id == item_description_table.c.feature_id
            )
        ).where(
            items_table.c.id == item_id
        ).group_by(
            items_table.c.id
        )
        return await conn.fetchrow(query)

    @staticmethod
    async def get_features(conn, feature_ids):
        if not feature_ids:
            return []
        query = select([
            item_features_table.c.id,
            item_features_table.c.description,
            item_features_table.c.embedding,
        ]).where(
            item_features_table.c.id.in_(feature_ids)
        )
        return await conn.fetch(query)

    # @staticmethod
    # def compute_embedding(features):
    #     if not features:
    #         return None
    #     embeddings = [f["embedding"] for f in features]
    #     return np.sum(np.array(embeddings), axis=0).tolist()

    @staticmethod
    async def create_item(conn, item_id, data):
        values = {k: v for k, v in data.items() if k != "features"}
        values["id"] = item_id
        query = items_table.insert().values(values)
        await conn.execute(query)

    @staticmethod
    async def create_item_description(conn, item_id, feature_ids):
        values = []
        for feature_id in feature_ids:
            values.append({"item_id": item_id,
                           "feature_id": feature_id})
        query = item_description_table.insert().values(values)
        await conn.execute(query)

    @staticmethod
    async def delete_item(conn, item_id):
        query = items_table.delete().where(
            items_table.c.id == item_id
        )
        await conn.execute(query)

    async def get(self):
        await self.check_item_exists()
        async with self.pg.transaction() as conn:
            item = await self.get_item(conn, self.item_id)
            # TODO Get features via one query
            item = dict(item)
            feature_ids = item.pop("feature_ids", [])
            item["features"] = await self.get_features(conn, feature_ids)
        return HTTPOk(body={"data": item})

    @request_schema(ItemSchema)
    async def put(self):
        async with self.pg.transaction() as conn:
            feature_ids = self.request["data"].pop("feature_ids")
            await self.create_item(conn, self.item_id, self.request["data"])
            await self.create_item_description(conn, self.item_id, feature_ids)
        return HTTPAccepted()

    async def delete(self):
        await self.check_item_exists()
        async with self.pg.transaction() as conn:
            await self.delete_item(conn, self.item_id)
        return HTTPNoContent()

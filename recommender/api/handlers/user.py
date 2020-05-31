import numpy as np
from aiohttp.web_exceptions import HTTPOk, HTTPAccepted, HTTPNoContent
from aiohttp_apispec import request_schema
from sqlalchemy import func, select

from recommender.api.schema import UserSchema
from recommender.db.schema import (
    users_table, user_features_table, user_description_table
)

from .base import BaseUserView


class UserView(BaseUserView):
    URL_PATH = r"/users/{user_id:\d+}"

    @staticmethod
    async def get_user(conn, user_id):
        query = select([
            users_table.c.id,
            func.vec_sum(
                user_features_table.c.embedding
            ).label("embedding"),
            func.array_remove(
                func.array_agg(user_features_table.c.id),
                None
            ).label("feature_ids")
        ]).select_from(
            users_table.outerjoin(
                user_description_table,
                users_table.c.id == user_description_table.c.user_id
            ).outerjoin(
                user_features_table,
                user_features_table.c.id == user_description_table.c.feature_id
            )
        ).where(
            users_table.c.id == user_id
        ).group_by(
            users_table.c.id
        )
        return await conn.fetchrow(query)

    @staticmethod
    async def get_features(conn, feature_ids):
        if not feature_ids:
            return []
        query = select([
            user_features_table.c.id,
            user_features_table.c.description,
            user_features_table.c.embedding,
        ]).where(
            user_features_table.c.id.in_(feature_ids)
        )
        return await conn.fetch(query)

    # @staticmethod
    # def compute_embedding(features):
    #     if not features:
    #         return None
    #     embeddings = [f["embedding"] for f in features]
    #     return np.sum(np.array(embeddings), axis=0).tolist()

    @staticmethod
    async def create_user(conn, user_id, data):
        values = {k: v for k, v in data.users() if k != "features"}
        values["id"] = user_id
        query = users_table.insert().values(values)
        await conn.execute(query)

    @staticmethod
    async def create_user_description(conn, user_id, feature_ids):
        values = []
        for feature_id in feature_ids:
            values.append({"user_id": user_id,
                           "feature_id": feature_id})
        query = user_description_table.insert().values(values)
        await conn.execute(query)

    @staticmethod
    async def delete_user(conn, user_id):
        query = users_table.delete().where(
            users_table.c.id == user_id
        )
        await conn.execute(query)

    async def get(self):
        await self.check_user_exists()
        async with self.pg.transaction() as conn:
            user = await self.get_user(conn, self.user_id)
            # TODO Get features via one query
            user = dict(user)
            feature_ids = user.pop("feature_ids", [])
            user["features"] = await self.get_features(conn, feature_ids)
        return HTTPOk(body={"data": user})

    @request_schema(UserSchema)
    async def put(self):
        async with self.pg.transaction() as conn:
            feature_ids = self.request["data"].pop("feature_ids")
            await self.create_user(conn, self.user_id, self.request["data"])
            await self.create_user_description(conn, self.user_id, feature_ids)
        return HTTPAccepted()

    async def delete(self):
        await self.check_user_exists()
        async with self.pg.transaction() as conn:
            await self.delete_user(conn, self.user_id)
        return HTTPNoContent()

from aiohttp.web_exceptions import HTTPOk
from aiohttp_apispec import querystring_schema

from recommender.api.schema import RecommendationQSSchema

from .base import BaseUserView


class UserRecommendationsView(BaseUserView):
    URL_PATH = r"/users/{user_id:\d+}/recommendations"

    @property
    def limit(self):
        return int(self.request["querystring"].get("limit", 10))

    @querystring_schema(RecommendationQSSchema)
    async def get(self):
        await self.check_user_exists()

        items = await self.redis.lrange(f"{self.user_id}", 0, self.limit)
        if not items:
            items = await self.redis.srandmember("latest", self.limit)

        items = [{"id": int(i.decode())} for i in items]
        return HTTPOk(body={"data": items})

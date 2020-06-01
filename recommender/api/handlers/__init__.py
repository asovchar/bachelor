from .item import ItemView
from .interactions import InteractionView
from .user import UserView
from .user_history import UserHistoryView
from .user_recommendations import UserRecommendationsView

HANDLERS = (
    ItemView, UserView, UserHistoryView,
    UserRecommendationsView, InteractionView,
)

from marshmallow import Schema
from marshmallow.fields import Dict, Int, List, Nested, Str
from marshmallow.validate import Range


class ItemSchema(Schema):
    feature_ids = List(Int(validate=Range(min=1), strict=True), default=[])


class UserSchema(Schema):
    feature_ids = List(Int(validate=Range(min=1), strict=True), default=[])


class HistoryQSSchema(Schema):
    limit = Int(validate=Range(min=1, max=100), default=10)


class RecommendationQSSchema(Schema):
    limit = Int(validate=Range(min=1, max=100), default=10)


class ErrorSchema(Schema):
    code = Str(required=True)
    message = Str(required=True)
    fields = Dict()


class ErrorResponseSchema(Schema):
    error = Nested(ErrorSchema(), required=True)

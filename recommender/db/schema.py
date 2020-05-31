from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    ARRAY, Float, Integer, Text
)

convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': 'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',
    'pk': 'pk__%(table_name)s'
}

metadata = MetaData(naming_convention=convention)

users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
)
items_table = Table(
    "items",
    metadata,
    Column("id", Integer, primary_key=True),
)
interactions_table = Table(
    "interactions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("item_id", Integer, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
)
user_features_table = Table(
    "user_features",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("description", Text, nullable=True),
    Column("embedding", ARRAY(Float), nullable=False),
)
item_features_table = Table(
    "item_features",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("description", Text, nullable=True),
    Column("embedding", ARRAY(Float), nullable=False),
)
user_description_table = Table(
    "user_description",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("feature_id", Integer, ForeignKey("user_features.id", ondelete="CASCADE"), primary_key=True),
)
item_description_table = Table(
    "item_description",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("item_id", Integer, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
    Column("feature_id", Integer, ForeignKey("item_features.id", ondelete="CASCADE"), primary_key=True),
)

import argparse
import logging

from aiomisc.log import LogFormat, basic_config
from configargparse import ArgumentParser
from lightfm import LightFM
from lightfm.datasets import fetch_stackexchange
from lightfm.evaluation import auc_score
from sqlalchemy import create_engine, select
from redis import Redis
from yarl import URL

from recommender.db.schema import (
    users_table,
    items_table,
    interactions_table,
    item_features_table,
    item_description_table,
)
from recommender.utils.argparse import clear_environ, positive_int
from recommender.utils.pg import DEFAULT_PG_URL, MAX_QUERY_ARGS
from recommender.utils.redis import DEFAULT_REDIS_URL

ENV_VAR_PREFIX = 'RECOMMENDER_'

NUM_THREADS = 1
NUM_COMPONENTS = 30
NUM_EPOCHS = 30
ITEM_ALPHA = 1e-6

log = logging.getLogger(__name__)

parser = ArgumentParser(
    auto_env_var_prefix=ENV_VAR_PREFIX, allow_abbrev=False,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

group = parser.add_argument_group('PostgreSQL options')
group.add_argument('--pg-url', type=URL, default=URL(DEFAULT_PG_URL),
                   help='URL to use to connect to the database')

group = parser.add_argument_group('Logging options')
group.add_argument('--log-level', default='info',
                   choices=('debug', 'info', 'warning', 'error', 'fatal'))
group.add_argument('--log-format', choices=LogFormat.choices(),
                   default='color')


def fetch_dataset():
    log.info("Fetching dataset")
    data = fetch_stackexchange("crossvalidated",
                               test_set_fraction=0.1,
                               indicator_features=False,
                               tag_features=True)
    train = data["train"]
    test = data["test"]
    item_features = data["item_features"]
    item_feature_labels = data["item_feature_labels"]

    # Remove duplicated train values from test set
    t1 = set(zip(*train.nonzero()))
    t2 = set(zip(*test.nonzero()))
    test = test.tocsr()
    for idx in t1 & t2:
        test[idx] = 0
    test = test.tocoo()

    return train, test, item_features, item_feature_labels


def fill_users_table(conn, matrix):
    log.info(f"Filling 'users' table")
    users = [{"id": i} for i in range(matrix.shape[0])]
    batch_size = MAX_QUERY_ARGS // len(users_table.c)
    for i in range(0, len(users), batch_size):
        query = users_table.insert().values(users[i:i+batch_size])
        conn.execute(query)


def fill_items_table(conn, matrix):
    log.info(f"Filling 'items' table")
    items = [{"id": i} for i in range(matrix.shape[1])]
    batch_size = MAX_QUERY_ARGS // len(items_table.c)
    for i in range(0, len(items), batch_size):
        query = items_table.insert().values(items[i:i+batch_size])
        conn.execute(query)


def fill_interactions_table(conn, matrix):
    log.info(f"Filling 'interactions' table")

    interactions = []
    rows, cols = matrix.nonzero()
    for u, i in zip(rows, cols):
        interactions.append({"user_id": int(u), "item_id": int(i)})

    batch_size = MAX_QUERY_ARGS // len(interactions_table.c)
    for i in range(0, len(interactions), batch_size):
        query = interactions_table.insert().values(interactions[i:i+batch_size])
        conn.execute(query)


def fill_item_features_table(conn, matrix, labels):
    log.info(f"Filling 'item_features' table")

    item_features = [
        {
            "id": i,
            "description": labels[i],
            "embedding": [0 for _ in range(i)] + [1] + [0 for _ in range(i + 1, matrix.shape[1])]
        }
        for i in range(matrix.shape[1])
    ]
    batch_size = MAX_QUERY_ARGS // len(item_features_table.c)
    for i in range(0, len(item_features), batch_size):
        query = item_features_table.insert().values(item_features[i:i + batch_size])
        conn.execute(query)


def fill_item_descriptions_table(conn, matrix):
    log.info(f"Filling 'item_description' table")

    item_descriptions = []
    rows, cols = matrix.nonzero()
    for i, f in zip(rows, cols):
        item_descriptions.append({"item_id": int(i), "feature_id": int(f)})

    batch_size = MAX_QUERY_ARGS // len(item_description_table.c)
    for i in range(0, len(item_descriptions), batch_size):
        query = item_description_table.insert().values(item_descriptions[i:i + batch_size])
        conn.execute(query)


def main():
    args = parser.parse_args()
    clear_environ(lambda i: i.startswith(ENV_VAR_PREFIX))
    basic_config(args.log_level, args.log_format, buffered=True)

    train, test, item_features, item_feature_labels = fetch_dataset()

    engine = create_engine(str(args.pg_url))
    try:
        with engine.begin() as conn:
            fill_users_table(conn, train)
            fill_items_table(conn, train)
            fill_interactions_table(conn, train)
            fill_interactions_table(conn, test)
            fill_item_features_table(conn, item_features, item_feature_labels)
            fill_item_descriptions_table(conn, item_features)
    finally:
        engine.dispose()

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

from recommender.utils.argparse import clear_environ, positive_int
from recommender.utils.pg import DEFAULT_PG_URL
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

group = parser.add_argument_group('Redis options')
group.add_argument('--redis-url', type=URL, default=URL(DEFAULT_REDIS_URL),
                   help='URL to use to connect to the cache')
group.add_argument("--redis-ttl", type=positive_int, default=3600,
                   help="TTL for cached values")

group = parser.add_argument_group('Logging options')
group.add_argument('--log-level', default='info',
                   choices=('debug', 'info', 'warning', 'error', 'fatal'))
group.add_argument('--log-format', choices=LogFormat.choices(),
                   default='color')


def fetch_training_data():
    log.info("Fetching training data")

    data = fetch_stackexchange("crossvalidated",
                               test_set_fraction=0.1,
                               indicator_features=False,
                               tag_features=True)
    train = data["train"]
    test = data["test"]
    user_features = None
    item_features = data["item_features"]

    # Remove duplicated train values from test set
    t1 = set(zip(*train.nonzero()))
    t2 = set(zip(*test.nonzero()))
    test = test.tocsr()
    for idx in t1 & t2:
        test[idx] = 0
    test = test.tocoo()

    return train, test, user_features, item_features


def train_model(train, test, user_features, item_features):
    log.info("Initializing model")
    model = LightFM(loss="warp",
                    item_alpha=ITEM_ALPHA,
                    no_components=NUM_COMPONENTS)

    log.info("Training model")
    model = model.fit(train,
                      user_features=user_features,
                      item_features=item_features,
                      epochs=NUM_EPOCHS,
                      num_threads=NUM_THREADS)

    log.info("Scoring")
    train_auc = auc_score(model,
                          train,
                          user_features=user_features,
                          item_features=item_features,
                          num_threads=NUM_THREADS).mean()
    log.info(f"Training set AUC: {train_auc}")
    test_auc = auc_score(model,
                         test,
                         train_interactions=train,
                         user_features=user_features,
                         item_features=item_features,
                         num_threads=NUM_THREADS).mean()
    log.info(f"Test set AUC: {test_auc}")
    return model


def fetch_latest_items():
    log.info("Fetching latest items")
    data = fetch_stackexchange("crossvalidated",
                               test_set_fraction=0.1,
                               indicator_features=False,
                               tag_features=True)
    train = data["train"]
    return list(reversed(range(train.shape[1])))


def fetch_active_users():
    log.info("Fetching active users")
    data = fetch_stackexchange("crossvalidated",
                               test_set_fraction=0.1,
                               indicator_features=False,
                               tag_features=True)
    train = data["train"]
    return list(reversed(range(train.shape[0])))


def predict(model, user_ids, item_ids, user_features, item_features, limit=100):
    log.info("Predicting")
    predictions = {}
    for user_id in user_ids:
        pred = model.predict(user_ids=user_id,
                             item_ids=item_ids,
                             user_features=user_features,
                             item_features=item_features)
        pred = pred.argsort()[-limit:][::-1]
        predictions[user_id] = pred.tolist()
        log.debug(f"Predicted for user {user_id}")
    log.info(f"Predicted for {len(predictions)} users")
    return predictions


def cache_predictions(conn, predictions, ttl):
    log.info("Caching predictions")
    pipe = conn.pipeline()
    for user_id, pred in predictions.items():
        pipe.rpush(f"{user_id}", *pred)
        pipe.expire(f"{user_id}", ttl)
    pipe.execute()
    log.info(f"Cached predictions for {len(predictions)} users")


def cache_latest_items(conn, items, ttl):
    log.info("Caching latest items")
    pipe = conn.pipeline()
    pipe.delete("latest")
    pipe.sadd("latest", *items)
    pipe.expire("latest", ttl)
    pipe.execute()
    log.info(f"Cached {len(items)} latest items")


def main():
    args = parser.parse_args()
    clear_environ(lambda i: i.startswith(ENV_VAR_PREFIX))

    basic_config(args.log_level, args.log_format, buffered=True)

    # engine = create_engine(args.pg_url)
    # try:
    #     with engine.begin() as conn:
    users = fetch_active_users()
    items = fetch_latest_items()
    train, test, user_features, item_features = fetch_training_data()
    # finally:
    #     engine.dispose()

    model = train_model(train, test, user_features, item_features)
    predictions = predict(model, users, items, user_features, item_features)

    with Redis.from_url(str(args.redis_url)) as r:
        cache_predictions(r, predictions, args.redis_ttl)
        cache_latest_items(r, items[:100], args.redis_ttl)


if __name__ == "__main__":
    main()

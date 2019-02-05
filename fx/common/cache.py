from flask import current_app
import logging
import ujson


logger = logging.getLogger(__name__)


def save_to_redis(data):
    """
    saves data to redis
    :param data:
    :return:
    """
    redis_store = current_app.redis_store
    try:
        json_data = ujson.dumps(data)

        # we push to 2 lists , one for global transactions and one for a specific currency
        with redis_store.pipeline() as pipe:
            pipe.lpush("transactions", json_data)
            pipe.lpush(data["currency"], json_data)

    except Exception as e:
        logger.exception(e)
        raise


def get_data(key, item_numbers):
    """
    retrieves data from redis
    :param data:
    :return:
    """
    redis_store = current_app.redis_store
    try:
        data = redis_store.lrange(key, 0, item_numbers)
        return [ujson.loads(item) for item in data]
    except Exception as e:
        logger.exception(e)
        raise
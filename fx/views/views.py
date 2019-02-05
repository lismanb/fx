# coding=utf-8
from flask import Blueprint, request, current_app
import logging
from fx.common import errors
import ujson
import requests
import pytz
import datetime
from fx.common import cache
from sqlalchemy import desc

logger = logging.getLogger(__name__)

bp = Blueprint('fx', __name__)
http_session = requests.session()


def safe_to_float(obj):
    try:
        return float(obj)
    except Exception as e:
        logger.debug(repr(e))


def validate_post_request(data):
    """
    validates the request body. It should probably reside somewhere else
    :param data:
    :return: tuple . data and error if there is any.
    """

    # we could look in all currency symbols to make it better, but I don't have all the symbols available
    resp = {}
    if "currency" in data and type(data["currency"]) is str and len(data["currency"]) == 3:
        resp["currency"] = data["currency"].upper()
    else:
        return None, errors.INVALID_SYMBOL

    if "amount" in data and type(safe_to_float(data["amount"])) in (int, float):
        resp["amount"] = safe_to_float(data["amount"])
    else:
        return None, errors.INVALID_AMOUNT

    return resp, None


def validate_get_request(data):
    """
    validates the GET request
    :param data:
    :return:
    """

    # we could look in all currency symbols to make it better, but I don't have all the symbols available
    resp = {}
    if "currency" in data and type(data["currency"]) is str and len(data["currency"]) == 3:
        resp["currency"] = data["currency"].upper()
    elif "currency" in data:
        return None, errors.INVALID_SYMBOL

    if "limit" in data and type(safe_to_float(data["limit"])) in (int, float):
        resp["limit"] = safe_to_float(data["limit"])
    elif "limit" in data:
        return None, errors.INVALID_AMOUNT

    return resp, None


@bp.route('/grab_and_save', methods=["POST"])
def save_rate():
    # circular dependency hack
    from fx.models.storage import Storage
    from fx.fxrates import db

    try:
        if request.is_json is False:
            return ujson.dumps(errors.BAD_REQUEST), 400

        data, error = validate_post_request(request.json)
        if error:
            return ujson.dumps(error), 400

        currency = data.get("currency").upper()
        amount = data.get("amount")

        oxr_resp = http_session.get(url="{}&symbols={}&pretty_print=false".format(current_app.config["OPENEXCHANGE_URL"],
                                                                             currency))
        oxr_data = oxr_resp.json()

        # save to the database
        st = Storage(
            currency=currency,
            amount=amount,
            rate=oxr_data["rates"][currency],
            rate_at=pytz.utc.localize(datetime.datetime.utcfromtimestamp(oxr_data["timestamp"])),
            created_at=pytz.utc.localize(datetime.datetime.utcnow()))
        st.amount_usd = round(amount * oxr_data["rates"][currency], 9)

        session = db.session()
        try:
            session.add(st)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.exception(e)
            raise
        finally:
            session.close()

        # write to redis
        cache.save_to_redis({
            "currency": currency,
            "amount_usd": st.amount_usd,
            "amount": st.amount,
            "rate_at": st.rate_at,
            "rate": st.rate,
            "created_at": st.created_at,
        })

        return "{}", 201

    except Exception as e:
        logger.exception(e)
        return ujson.dumps(errors.INTERNAL_SERVER_ERROR), 500

def make_dict(storage_obj):
    """

    :param storage_obj:
    :return:
    """
    resp = dict()
    resp["created_at"] = storage_obj.created_at
    resp["created_at"] = storage_obj.created_at
    resp["rate"] = storage_obj.rate
    resp["currency"] = storage_obj.currency
    resp["amount"] = storage_obj.amount
    resp["amount_usd"] = storage_obj.amount_usd

    return resp


@bp.route('/last', methods=["GET"])
def get_last_transactions():
    # circular dependency hack
    from fx.models.storage import Storage
    from fx.fxrates import db

    try:
        data, error = validate_get_request(request.args)
        if error:
            return ujson.dumps(error), 400

        currency = data.get("currency").upper()
        limit = data.get("limit", 1)
        if limit > 100:
            limit = 100

        session = db.session()
        data = []
        try:
            if currency is not None:
                db_data = session.query(Storage).filter(currency==currency).order_by(desc(Storage.created_at)).limit(limit).all()
                redis_data = cache.get_data(currency, limit)
            else:
                db_data = session.query(Storage).order_by(desc(Storage.created_at)).limit(limit).all()
                redis_data = cache.get_data("transactions", limit)
        except Exception as e:
            session.rollback()
            logger.exception(e)
            raise

        db_data = [make_dict(item) for item in db_data]

        return {
            "request": request.args,
            "data":[
                {"source": "mysql", "transactions": db_data},
                {"source": "redis", "transactions": redis_data}
            ]}

    except Exception as e:
        logger.exception(e)
        return ujson.dumps(errors.INTERNAL_SERVER_ERROR), 500
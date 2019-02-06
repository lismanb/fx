# coding=utf-8
import datetime
import logging
import ujson
from flask import Response
import pytz
import requests
from flask import Blueprint, request, current_app
from sqlalchemy import desc

from fx.common import cache
from fx.common import errors
from fx.database.db import session_scope
from fx.models.storage import Transactions

logger = logging.getLogger(__name__)

bp = Blueprint('fx', __name__)
http_session = requests.session()


def safe_to_float(obj):
    try:
        return float(obj)
    except Exception as e:
        logger.debug(repr(e))


def safe_to_int(obj):
    """
    returns the integer value or none
    :param obj:
    :return:
    """
    try:
        return int(obj)
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

    if "limit" in data and type(safe_to_int(data["limit"])) is int:
        resp["limit"] = safe_to_int(data["limit"])
    elif "limit" in data:
        return None, errors.INVALID_AMOUNT

    return resp, None


@bp.route('/grab_and_save', methods=["POST"])
def save_rate():
    try:
        if request.is_json is False:
            return Response(ujson.dumps(errors.BAD_REQUEST), 400, content_type='application/json')

        data, error = validate_post_request(request.json)
        if error:
            return Response(ujson.dumps(error), 400, content_type='application/json')

        currency = data.get("currency").upper()
        amount = data.get("amount")

        oxr_resp = http_session.get(url="{}&symbols={}&pretty_print=false".format(current_app.config["OPENEXCHANGE_URL"],
                                                                             currency))
        oxr_data = oxr_resp.json()

        with session_scope() as session:
            # save to the database
            st = Transactions(
                currency=currency,
                amount=amount,
                rate=oxr_data["rates"][currency],
                rate_at=pytz.utc.localize(datetime.datetime.utcfromtimestamp(oxr_data["timestamp"])),
                created_at=pytz.utc.localize(datetime.datetime.utcnow()))
            st.amount_usd = round(amount * oxr_data["rates"][currency], 9)

            session.add(st)
            session.commit()

            # write to redis
            cache.save_to_redis({
                "currency": currency,
                "amount_usd": st.amount_usd,
                "amount": st.amount,
                "rate_at": st.rate_at,
                "rate": st.rate,
                "created_at": st.created_at,
            })

        return Response("{}", 201, content_type='application/json')

    except Exception as e:
        logger.exception(e)
        return Response(ujson.dumps(errors.INTERNAL_SERVER_ERROR), 500, content_type='application/json')

def make_dict(storage_obj):
    """

    :param storage_obj:
    :return:
    """
    resp = dict()
    resp["created_at"] = storage_obj.created_at
    resp["created_at"] = storage_obj.created_at
    resp["rate"] = storage_obj.rate
    resp["rate_at"] = storage_obj.rate_at
    resp["currency"] = storage_obj.currency
    resp["amount"] = storage_obj.amount
    resp["amount_usd"] = storage_obj.amount_usd

    return resp


@bp.route('/last', methods=["GET"])
def get_last_transactions():
    # circular dependency hack

    try:
        data, error = validate_get_request(request.args)
        if error:
            return Response(ujson.dumps(error), 400, content_type='application/json')

        currency = data.get("currency", '').upper()
        limit = data.get("limit", 1)
        if limit > 100:
            limit = 100

        with session_scope() as session:
            if currency:
                db_data = session.query(Transactions).filter(currency==currency).order_by(desc(Transactions.created_at)).limit(limit).all()[:]
                redis_data = cache.get_data(currency, limit)
            else:
                db_data = session.query(Transactions).order_by(desc(Transactions.created_at)).limit(limit).all()[:]
                redis_data = cache.get_data("transactions", limit-1)

            db_data = [make_dict(item) for item in db_data]

        return Response(ujson.dumps({
            "request": request.args,
            "data":[
                {"source": "mysql", "transactions": db_data},
                {"source": "redis", "transactions": redis_data}
            ]}), 200, content_type='application/json')

    except Exception as e:
        logger.exception(e)
        return Response(ujson.dumps(errors.INTERNAL_SERVER_ERROR), 500, content_type='application/json')

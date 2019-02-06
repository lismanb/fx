import pytest
from flask import g, session
from fx.fxrates import db
import ujson


def test_grab_and_save(client, app):
    # test that viewing the page renders without template errors
    assert client.post('/fx/grab_and_save',
                       data=ujson.dumps({"currency":"MXN", "amount":"500"}),
                       headers={"Content-Type":"application/json"}).status_code == 201

    assert client.post('/fx/grab_and_save',
                       data=ujson.dumps({"currency": "MXN", "amount": "500"}),
                       headers={"Content-Type": "application/json"}).json == {}

    resp = client.get('/fx/last').json
    if resp["data"][0]["source"] == 'mysql':
        db_transactions = resp["data"][0]["transactions"]
        redis_transactions = resp["data"][1]["transactions"]
    else:
        db_transactions = resp["data"][1]["transactions"]
        redis_transactions = resp["data"][0]["transactions"]

    assert len(db_transactions) == len(redis_transactions)

    for db1, red1 in zip(db_transactions, redis_transactions):
        assert len(db1) == len(red1)

        for k in db1:
            assert db1[k] == red1[k]

########################
# OTHER tests
#######################

# get last without anything in redis or db
# save 2 transaction on different currencies and test if the last with currency and without + offset returns the correct response
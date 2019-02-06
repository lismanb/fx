import os
import tempfile

import pytest
from fx.fxrates import create_app
from fx.fxrates import db, init_db

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    # create the app with common test config
    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///{}'.format(db_path),
        'REDIS_URL': 'redis://localhost:6379/1'
    })

    # create the database and load test data
    with app.app_context():
        with app.open_resource('database/init_schema.sql') as f:
            db.session.execute("""CREATE TABLE transactions (
                  id INTEGER PRIMARY KEY,
                  currency CHAR(3) NOT NULL ,
                  rate REAL NOT NULL ,
                  amount REAL NOT NULL ,
                  amount_usd REAL NOT NULL ,
                  rate_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
                  )""")

    yield app

    # close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

    redis_store = app.extensions['redis'].flushdb()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()
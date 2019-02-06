from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from fx.common import errors
from fx.views import views
import ujson
import click
from flask.cli import with_appcontext
from flask import current_app


db = SQLAlchemy()
redis_store = FlaskRedis()

def init_db(app):
    """Clear existing data and create new tables."""
    with app.open_resource('database/init_schema.sql') as f:
        db.session.execute(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db(current_app)
    click.echo('Initialized the database.')


def create_app():
    app = Flask(__name__)
    app.config.from_envvar('FXRATES_SETTINGS')
    db.init_app(app)
    redis_store.init_app(app)

    app.register_blueprint(views.bp, url_prefix='/fx')

    @app.errorhandler(404)
    def not_found(status):
        return ujson.dumps(errors.RESOURCE_NOT_FOUND), 404

    @app.errorhandler(405)
    def method_not_allowed(status):
        return ujson.dumps(errors.METHOD_NOT_ALLOWED), 405

    @app.errorhandler(500)
    def method_not_allowed(status):
        return ujson.dumps(errors.INTERNAL_SERVER_ERROR), 500

    app.cli.add_command(init_db_command)

    return app
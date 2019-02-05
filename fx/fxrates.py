from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from fx.common import errors
from fx.views import views
import ujson


app = Flask(__name__)
app.config.from_envvar('FXRATES_SETTINGS')

db = SQLAlchemy(app)
redis_store = FlaskRedis(app)

app.register_blueprint(views.bp, url_prefix='/fx')

@app.errorhandler(404)
def not_found(status):
    return ujson.dumps(errors.RESOURCE_NOT_FOUND), 404

@app.errorhandler(405)
def method_not_allowed(status):
    return ujson.dumps(errors.METHOD_NOT_ALLOWED), 405

redis_store.init_app(app)
db.init_app(app)


if __name__ == '__main__':
    from flask_migrate import Migrate
    Migrate(app, db)
    app.run()

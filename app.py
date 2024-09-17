from flask import Flask
from utils.models import db, models
from utils.routes import api
from utils.helper import auth, jwt
from celery_config import celery
from flask_cors import CORS
from datetime import timedelta

app = Flask(__name__)

CORS(app, resources={
    r"/*" : {
    "origins":
        "*"
        }
    }
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
	)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:first@localhost:5432/postgres"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = "mysecretkey"
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

db.init_app(app)
jwt.init_app(app)

app.register_blueprint(models)
app.register_blueprint(api)
app.register_blueprint(auth)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug = True)
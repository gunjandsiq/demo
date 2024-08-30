from flask import Flask
from utils.models import db, models
from utils.routes import api
from flask_cors import CORS


app = Flask(__name__)
CORS(app) 
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:first@localhost:5432/postgres"

db.init_app(app)

app.register_blueprint(models)
app.register_blueprint(api)

if __name__=='__main__':
    app.run(debug=True)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:111111@localhost/karaokedb?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'secret'

db = SQLAlchemy(app=app)
login = LoginManager(app=app)

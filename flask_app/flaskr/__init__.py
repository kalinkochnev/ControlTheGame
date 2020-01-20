import os
from flask import Flask

def create_app(test_config=None):
    #Create app and configure
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)

    from . import database as db
    db.init_app(app)
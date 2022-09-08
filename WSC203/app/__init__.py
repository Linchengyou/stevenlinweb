from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_babel import Babel, lazy_gettext as _l
from flask_moment import Moment

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

login = LoginManager()
login.init_app(app)
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page')
login.session_protection = "strong"
bootstrap = Bootstrap(app)
babel = Babel(app)
moment = Moment(app)

from app import models
from app.view import views
from app.view.auth_view import auth_blueprint
from app.view.func_view import func_blueprint
from app.view.qc_view import qc_blueprint
app.register_blueprint(auth_blueprint)
app.register_blueprint(func_blueprint)
app.register_blueprint(qc_blueprint)

"""
if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler('tmp/web.log', 'a', 1 * 1024 * 1024, 2)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('web startup')
"""

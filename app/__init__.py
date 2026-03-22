from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from flask_wtf.csrf import CSRFProtect

# The instances are created here; they will be imported by models.py
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # Configuration de Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'login' # Redirige ici si l'user n'est pas connecté
    login_manager.login_message_category = 'info'

    csrf.init_app(app)

    with app.app_context():
        # We import the models so that SQLAlchemy can save them
        from . import models, routes

        @login_manager.user_loader
        def load_user(user_id):
            return models.User.query.get(int(user_id))

    return app
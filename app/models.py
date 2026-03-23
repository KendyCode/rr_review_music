from . import db  # On importe l'instance db créée dans __init__.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime



class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    is_admin = db.Column(db.Boolean, default=False)

    # Relation : Un utilisateur peut écrire plusieurs avis
    reviews = db.relationship('Review', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Track(db.Model):
    __tablename__ = 'tracks'
    id = db.Column(db.Integer, primary_key=True)
    deezer_id = db.Column(db.String(100), unique=True, nullable=False) # ID unique venant de l'API
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200), nullable=False)
    cover_medium = db.Column(db.String(300)) # URL de l'image de l'album

    # Relation : Un morceau peut avoir plusieurs avis
    # cascade="all, delete-orphan" pour supprimer les avis si la musique est supprimée
    reviews = db.relationship('Review', backref='track', lazy=True, cascade="all, delete-orphan")

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False) # Note de 1 à 5
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

    # Clés étrangères
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('tracks.id'), nullable=False)
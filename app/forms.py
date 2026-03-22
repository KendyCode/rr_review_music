from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class SearchForm(FlaskForm):
    search = StringField('Chercher un artiste ou un titre', validators=[DataRequired()])
    submit = SubmitField('Rechercher')

class ReviewForm(FlaskForm):
    content = TextAreaField('Votre avis', validators=[DataRequired(), Length(min=5, max=500)])
    rating = IntegerField('Note (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Publier')

class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')
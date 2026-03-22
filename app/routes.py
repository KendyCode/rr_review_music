import requests
from flask import render_template, flash, redirect, url_for, request
from . import db
from .models import Track, Review, User
from .forms import SearchForm, ReviewForm
from flask_login import current_user, login_required, login_user, logout_user
from flask import current_app as app
from .forms import LoginForm, RegistrationForm # Assure-toi d'avoir créé ce formulaire dans forms.py

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('search'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # On vérifie si l'utilisateur existe déjà
        user_exists = User.query.filter_by(email=form.email.data).first()
        if user_exists:
            flash('Cet email est déjà utilisé.', 'danger')
            return redirect(url_for('register'))

        # Création du nouvel utilisateur
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data) # Hachage automatique ici

        db.session.add(user)
        db.session.commit()

        flash('Compte créé avec succès ! Vous pouvez vous connecter.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('search'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('search'))
        else:
            flash('Email ou mot de passe incorrect.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('search'))

@app.route('/my-reviews')
@login_required
def my_reviews():
    # current_user.reviews fonctionne grâce au backref='author' dans le modèle User
    user_reviews = current_user.reviews
    return render_template('my_reviews.html', reviews=user_reviews)

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    results = []
    if form.validate_on_submit():
        query = form.search.data
        # Appel à l'API Deezer
        response = requests.get(f"https://api.deezer.com/search?q={query}")
        if response.status_code == 200:
            results = response.json().get('data', [])
    return render_template('search.html', form=form, results=results)

@app.route('/review/<int:deezer_id>', methods=['GET', 'POST'])
@login_required # Sécurité : il faut être connecté pour noter
def add_review(deezer_id):
    form = ReviewForm()

    # 1. On vérifie si la musique existe déjà en BDD
    track = Track.query.filter_by(deezer_id=str(deezer_id)).first()

    # 2. Si elle n'existe pas, on va chercher ses infos sur l'API Deezer
    if not track:
        response = requests.get(f"https://api.deezer.com/track/{deezer_id}")
        if response.status_code == 200:
            data = response.json()
            track = Track(
                deezer_id=str(deezer_id),
                title=data['title'],
                artist=data['artist']['name'],
                cover_medium=data['album']['cover_medium']
            )
            db.session.add(track)
            db.session.commit()
        else:
            flash("Musique introuvable sur Deezer.", "danger")
            return redirect(url_for('search'))

    # 3. Traitement du formulaire d'avis
    if form.validate_on_submit():
        new_review = Review(
            content=form.content.data,
            rating=form.rating.data,
            user_id=current_user.id,
            track_id=track.id
        )
        db.session.add(new_review)
        db.session.commit()
        flash("Votre avis a été ajouté !", "success")
        return redirect(url_for('search')) # Ou vers la page de profil

    return render_template('add_review.html', form=form, track=track)

import requests
from flask import render_template, flash, redirect, url_for, request
from . import db
from .models import Track, Review, User
from .forms import SearchForm, ReviewForm
from flask_login import current_user, login_required, login_user, logout_user
from flask import current_app as app
from .forms import LoginForm, RegistrationForm # Assure-toi d'avoir créé ce formulaire dans forms.py
from functools import wraps
from flask import abort
import os

if os.getenv("USE_PROXY") == "True":
    proxies = {"http": "http://172.16.0.51:8080", "https": "http://172.16.0.51:8080"}
else:
    proxies = None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403) # Accès interdit
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    all_reviews = Review.query.order_by(Review.date_posted.desc()).all()
    all_tracks = Track.query.all()
    return render_template('admin/dashboard.html', reviews=all_reviews, tracks=all_tracks)

# --- CRUD TRACKS POUR ADMIN ---

@app.route('/admin/track/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_track():
    # Ici, tu peux créer un formulaire manuel ou réutiliser la logique Deezer
    # Mais pour un admin, on peut vouloir ajouter un titre "Hors API"
    if request.method == 'POST':
        new_track = Track(
            deezer_id=request.form.get('deezer_id'),
            title=request.form.get('title'),
            artist=request.form.get('artist'),
            cover_medium=request.form.get('cover_url')
        )
        db.session.add(new_track)
        db.session.commit()
        flash("Track ajoutée manuellement !", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/edit_track.html', track=None)

@app.route('/admin/track/delete/<int:track_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_track(track_id):
    track = Track.query.get_or_404(track_id)
    # Attention : Supprimer une track supprimera ses reviews en cascade (si configuré)
    db.session.delete(track)
    db.session.commit()
    flash("Track et ses avis supprimés.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/track/edit/<int:track_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_track(track_id):
    track = Track.query.get_or_404(track_id)

    if request.method == 'POST':
        track.title = request.form.get('title')
        track.artist = request.form.get('artist')
        track.deezer_id = request.form.get('deezer_id')
        track.cover_medium = request.form.get('cover_url')

        db.session.commit()
        flash(f"Le titre '{track.title}' a été mis à jour.", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/edit_track.html', track=track)

@app.route('/')
def index():
    # Optionnel : Afficher les 5 derniers avis publics sur le site
    latest_reviews = Review.query.order_by(Review.date_posted.desc()).limit(5).all()
    return render_template('index.html', reviews=latest_reviews)

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
        response = requests.get(f"https://api.deezer.com/search?q={query}",proxies=proxies, timeout=5)
        print(response.json())
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
        response = requests.get(f"https://api.deezer.com/track/{deezer_id}",proxies=proxies, timeout=5)
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

@app.route('/review/edit/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)

    # SÉCURITÉ : Vérifier que l'auteur est bien l'utilisateur connecté
    if review.author != current_user and not current_user.is_admin:
        flash("Vous n'avez pas l'autorisation de modifier cet avis.", "danger")
        return redirect(url_for('my_reviews'))

    form = ReviewForm()

    if form.validate_on_submit():
        review.content = form.content.data
        review.rating = form.rating.data
        db.session.commit()
        flash("L'avis a été mis à jour par l'administration." if current_user.is_admin else "L'avis a été avis a été mis à jour !", "success")
        return redirect(request.referrer or url_for('index'))

    # Pré-remplir le formulaire avec les données actuelles
    elif request.method == 'GET':
        form.content.data = review.content
        form.rating.data = review.rating

    return render_template('edit_review.html', form=form, track=review.track)

@app.route('/review/delete/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)

    # SÉCURITÉ : Vérifier que l'auteur est bien l'utilisateur connecté
    if review.author != current_user and not current_user.is_admin:
        flash("Action non autorisée.", "danger")
        return redirect(url_for('my_reviews'))

    db.session.delete(review)
    db.session.commit()
    flash("L'avis a été supprimé par l'administration." if current_user.is_admin else "L'avis a été supprimé.", "info")
    return redirect(request.referrer or url_for('index'))

@app.route('/track/<int:deezer_id>')
def track_details(deezer_id):
    # 1. On récupère les infos Deezer (pour l'audio preview qui n'est pas en BDD)
    response = requests.get(f"https://api.deezer.com/track/{deezer_id}",proxies=proxies, timeout=5)
    track_api = response.json() if response.status_code == 200 else None

    print(track_api.get("album").get("cover_big"))

    # 2. On cherche dans notre BDD
    track_in_db = Track.query.filter_by(deezer_id=str(deezer_id)).first()


    reviews = []
    display_track = track_api # Par défaut, on utilise l'API

    if track_in_db:
        # On récupère les avis
        reviews = Review.query.filter_by(track_id=track_in_db.id).order_by(Review.date_posted.desc()).all()

        # SÉCURITÉ : On remplace les infos de l'API par celles de notre BDD
        # On garde track_api pour le preview sonore car il n'est pas en BDD
        display_track = {
            'title': track_in_db.title,
            'artist': {'name': track_in_db.artist},
            'album': {'cover_big': track_api.get("album").get("cover_big") if track_api else track_in_db.cover_medium},
            'preview': track_api.get('preview') if track_api else None,
            'id': track_in_db.deezer_id
        }

    return render_template('track_details.html', track=display_track, reviews=reviews)
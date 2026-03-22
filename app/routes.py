import requests
from flask import render_template, request, redirect, url_for, flash
from . import db
from .models import Track, Review, User
from .forms import SearchForm, ReviewForm
from flask import current_app as app

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
def add_review(deezer_id):
    pass

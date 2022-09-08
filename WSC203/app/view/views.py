from app import app, db, login, babel
from flask import request, g, session
from app.models import User
from flask_login import current_user
from config import LANGUAGES
from babel import negotiate_locale
from datetime import datetime


@app.before_request
def before_request():
    if session.get('lang_value') is None:
        lang_key = get_browser_lang()
        if lang_key in LANGUAGES:
            session['lang_value'] = LANGUAGES[lang_key]

    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


@babel.localeselector
def get_locale():
    try:
        lang = session['lang_key']
    except KeyError:
        lang = None
    if lang is not None:
        return lang

    return get_browser_lang()


def get_browser_lang():
    preferred = [x[0:2] for x in request.accept_languages.values()]
    return negotiate_locale(preferred, LANGUAGES.keys())

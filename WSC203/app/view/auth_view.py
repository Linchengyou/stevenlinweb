from flask import Blueprint, render_template, flash, redirect, url_for, g
from flask_login import login_user, logout_user, login_required
from app.models import User
from app.form import LoginForm, ProfileForm, PasswordResetForm
from flask_babel import _, lazy_gettext as _l
from app import db

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route('/', methods=['GET', 'POST'])
@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # if g.user is not None and g.user.is_authenticated:
    #     print(g.user)
    #     return redirect(url_for('func.network_setting'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_l('Invalid username or password'), 'alert-danger')
            return redirect(url_for('auth.login'))
        login_user(user)
        return redirect(url_for('func.network_setting'))
    return render_template('login.html', title='Sign In', form=form)


@auth_blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        g.user.set_password(form.new_pwd.data)
        db.session.commit()
        flash(_l('Change successful!'), 'alert-success')
        return redirect(url_for('auth.profile'))
    return render_template('profile_edit.html', title='Profile Edit', form=form)


@auth_blueprint.route('/password_reset', methods=['GET', 'POST'])
@login_required
def password_reset():
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username='admin').first()
        user.set_password('admin')
        db.session.commit()
        flash(_l('Change successful!'), 'alert-success')
        return redirect(url_for('auth.password_reset'))
    return render_template('password_reset.html', title='Password Reset', form=form)


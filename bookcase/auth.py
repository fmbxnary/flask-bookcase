import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from bookcase.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


# user register
@bp.route('/register', methods=('GET', 'POST'))
def register():
    jobs = ['Student', 'Computer Engineer', 'Psychologist']

    if g.user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password1 = request.form['password1']
        password2 = request.form['password2']
        job = request.form['job']
        fav_author = request.form['fav_author']

        db = get_db()
        error = None

        # ensure user inputs are valid
        if not username:
            error = 'Username is required.'
        elif len(username) < 3:
            error = 'username is too short.'
        elif len(username) > 20:
            error = 'username is too long.'
        elif not email:
            error = 'Email is required.'
        elif not password1:
            error = 'Password is required.'
        elif not password2:
            error = 'Password (Confirm) is required.'
        elif not len(password1) >= 8:
            error = 'Password is too short.'
        elif not password1 == password2:
            error = 'Passwords do not match.'
        elif job not in jobs:
            error = 'Job must be provided'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user"
                    " (username, email, job, password, fav_author)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (
                        username,
                        email,
                        job,
                        generate_password_hash(password1),
                        fav_author
                    ),
                )
                flash("Registration is successful", category='success')
                db.commit()
            except db.IntegrityError:
                error = f"User {username} or {email} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error, category='error')

    return render_template('auth/register.html', jobs=jobs)


# login user
@bp.route('/login', methods=('GET', 'POST'))
def login():

    # if not logged in try to log in
    if not g.user:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            db = get_db()
            error = None
            user = db.execute(
                'SELECT * FROM user WHERE username = ?', (username,)
            ).fetchone()

            # ensure user is exist
            if user is None:
                error = 'Incorrect username.'
            # ensure passwords match
            elif not check_password_hash(user['password'], password):
                error = 'Incorrect password.'

            # login user if all conditions passed
            if error is None:
                session.clear()
                session['user_id'] = user['id']
                return redirect(url_for('index'))

            # flash error if any
            flash(error, category='error')

        return render_template('auth/login.html')
    return redirect(url_for('index'))


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


# logout user
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

import secrets
from flask import Blueprint, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from db import db
from models import User
from forms import LoginForm, RegisterForm
from extensions import oauth

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("main.landing"))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.username.data.strip()
        user = (
            User.query.filter_by(username=identifier).first()
            or User.query.filter_by(email=identifier).first()
        )
        if user and user.check_password(form.password.data):
            session["logged_in"] = True
            session["is_admin"] = user.is_admin
            session["username"] = user.username
            session["user_id"] = user.id
            flash(f"Welcome back, {user.full_name.split()[0]}!", "success")
            return redirect(
                url_for("admin.admin_panel") if user.is_admin else url_for("user.dashboard")
            )
        flash("Invalid username or password.", "danger")

    return render_template("screens/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("logged_in"):
        return redirect(url_for("main.landing"))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            form.username.errors.append("That username is already taken.")
        elif User.query.filter_by(email=form.email.data).first():
            form.email.errors.append("An account with that email already exists.")
        else:
            user = User(
                full_name=form.full_name.data.strip(),
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("screens/register.html", form=form)


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.landing"))


@auth_bp.route("/login/google")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/login/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    user_info = token.get("userinfo")
    if not user_info:
        flash("Google sign-in failed. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    google_id = user_info["sub"]
    email = user_info["email"]

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
            db.session.commit()
        else:
            full_name = user_info.get("name", email.split("@")[0])
            base_username = email.split("@")[0].lower().replace(".", "_")
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            user = User(
                full_name=full_name,
                username=username,
                email=email,
                google_id=google_id,
                password_hash=generate_password_hash(secrets.token_hex(32)),
            )
            db.session.add(user)
            db.session.commit()

    session["logged_in"] = True
    session["is_admin"] = user.is_admin
    session["username"] = user.username
    session["user_id"] = user.id
    flash(f"Welcome, {user.full_name.split()[0]}!", "success")
    return redirect(
        url_for("admin.admin_panel") if user.is_admin else url_for("user.dashboard")
    )

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from db import db
from models import User, Recipe, Review, Favourite
from forms import ProfileForm, PasswordForm

user_bp = Blueprint("user", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to view that page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@user_bp.route("/dashboard")
@login_required
def dashboard():
    user = User.query.get_or_404(session["user_id"])

    fav_count = user.favourite_list.count()
    review_count = user.review_list.count()

    stats = {
        "favourites": fav_count,
        "reviews": review_count,
        "recipes_tried": review_count,
        "streak": min(review_count, 7),
    }

    recent_reviews = (
        user.review_list.order_by(Review.created_at.desc()).limit(3).all()
    )
    recent_favs = (
        user.favourite_list.order_by(Favourite.created_at.desc()).limit(2).all()
    )

    activity = []
    for rev in recent_reviews:
        activity.append({
            "icon": "bi-chat-dots-fill",
            "icon_bg": "#E0F4EC",
            "icon_color": "var(--naija-green)",
            "text": f"You reviewed <strong>{rev.recipe.title}</strong> — gave it {rev.rating} stars",
            "date": rev.created_at.strftime("%-d %b %Y"),
            "action_url": url_for("main.recipe_detail", slug=rev.recipe.slug),
            "action_label": "View",
        })
    for fav in recent_favs:
        activity.append({
            "icon": "bi-heart-fill",
            "icon_bg": "#FFE0E0",
            "icon_color": "var(--naija-red)",
            "text": f"You favourited <strong>{fav.recipe.title}</strong>",
            "date": fav.created_at.strftime("%-d %b %Y"),
            "action_url": url_for("main.recipe_detail", slug=fav.recipe.slug),
            "action_label": "View",
        })

    activity.sort(key=lambda x: x["date"], reverse=True)

    return render_template(
        "screens/dashboard.html",
        user=user,
        stats=stats,
        activity=activity,
    )


@user_bp.route("/favourites")
@login_required
def favourites():
    user = User.query.get_or_404(session["user_id"])
    fav_recipes = [
        f.recipe for f in
        user.favourite_list.order_by(Favourite.created_at.desc()).all()
    ]
    return render_template("screens/favourites.html", recipes=fav_recipes)


@user_bp.route("/my-reviews")
@login_required
def my_reviews():
    user = User.query.get_or_404(session["user_id"])
    reviews = user.review_list.order_by(Review.created_at.desc()).all()
    return render_template("screens/my_reviews.html", reviews=reviews)


@user_bp.route("/my-reviews/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != session["user_id"]:
        flash("You cannot delete that review.", "danger")
        return redirect(url_for("user.my_reviews"))
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted.", "success")
    return redirect(url_for("user.my_reviews"))


@user_bp.route("/settings", methods=["GET"])
@login_required
def user_settings():
    user = User.query.get_or_404(session["user_id"])
    profile_form = ProfileForm(obj=user)
    password_form = PasswordForm()
    return render_template(
        "screens/user_settings.html",
        user=user,
        profile_form=profile_form,
        password_form=password_form,
    )


@user_bp.route("/settings/profile", methods=["POST"])
@login_required
def update_profile():
    user = User.query.get_or_404(session["user_id"])
    form = ProfileForm()
    if form.validate_on_submit():
        new_username = form.username.data.strip()
        new_email = form.email.data.strip().lower()

        conflict_u = User.query.filter(
            User.username == new_username, User.id != user.id
        ).first()
        conflict_e = User.query.filter(
            User.email == new_email, User.id != user.id
        ).first()

        if conflict_u:
            flash("That username is already taken.", "danger")
        elif conflict_e:
            flash("That email is already in use.", "danger")
        else:
            user.full_name = form.full_name.data.strip()
            user.username = new_username
            user.email = new_email
            user.location = form.location.data.strip() if form.location.data else None
            user.bio = form.bio.data.strip() if form.bio.data else None
            db.session.commit()
            session["username"] = user.username
            flash("Profile updated successfully.", "success")
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")

    return redirect(url_for("user.user_settings"))


@user_bp.route("/settings/password", methods=["POST"])
@login_required
def update_password():
    user = User.query.get_or_404(session["user_id"])
    form = PasswordForm()
    if form.validate_on_submit():
        if not user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            user.set_password(form.new_password.data)
            db.session.commit()
            flash("Password updated successfully.", "success")
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")

    return redirect(url_for("user.user_settings"))


@user_bp.route("/settings/delete", methods=["POST"])
@login_required
def delete_account():
    user = User.query.get_or_404(session["user_id"])
    db.session.delete(user)
    db.session.commit()
    session.clear()
    flash("Your account has been permanently deleted.", "info")
    return redirect(url_for("main.landing"))

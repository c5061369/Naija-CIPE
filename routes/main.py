from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from db import db
from models import Recipe, Category, Store, Review, Favourite
from forms import ReviewForm
from sqlalchemy import or_, func

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def landing():
    featured = (
        Recipe.query.filter_by(status="published")
        .order_by(Recipe.created_at.desc())
        .limit(4)
        .all()
    )
    categories = Category.query.order_by(Category.name).all()
    return render_template("screens/landing.html", featured_recipes=featured, categories=categories)


@main_bp.route("/recipes")
def browse():
    page = request.args.get("page", 1, type=int)
    per_page = 12
    sort_by = request.args.get("sort", "popular")
    q = request.args.get("q", "").strip()
    selected_cats = request.args.getlist("cat")
    selected_diffs = request.args.getlist("diff")
    max_time = request.args.get("time", 180, type=int)

    query = Recipe.query.filter_by(status="published")

    if q:
        query = query.filter(
            or_(Recipe.title.ilike(f"%{q}%"), Recipe.description.ilike(f"%{q}%"))
        )
    if selected_cats:
        query = query.join(Category).filter(Category.name.in_(selected_cats))
    if selected_diffs:
        query = query.filter(Recipe.difficulty.in_(selected_diffs))
    if max_time < 180:
        query = query.filter((Recipe.prep_time + Recipe.cook_time) <= max_time)

    if sort_by == "newest":
        query = query.order_by(Recipe.created_at.desc())
    elif sort_by == "quickest":
        query = query.order_by((Recipe.prep_time + Recipe.cook_time).asc())
    else:
        query = query.order_by(Recipe.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.order_by(Category.name).all()

    return render_template(
        "screens/browse.html",
        recipes=pagination.items,
        pagination=pagination,
        total=pagination.total,
        sort_by=sort_by,
        categories=categories,
    )


@main_bp.route("/recipes/<slug>")
def recipe_detail(slug):
    recipe = Recipe.query.filter_by(slug=slug, status="published").first_or_404()
    related = (
        Recipe.query.filter(
            Recipe.category_id == recipe.category_id,
            Recipe.id != recipe.id,
            Recipe.status == "published",
        )
        .limit(3)
        .all()
    )

    review_form = ReviewForm()

    user_has_reviewed = False
    user_has_favourited = False
    if session.get("logged_in"):
        user_id = session.get("user_id")
        user_has_reviewed = (
            Review.query.filter_by(recipe_id=recipe.id, user_id=user_id).first() is not None
        )
        user_has_favourited = (
            Favourite.query.filter_by(recipe_id=recipe.id, user_id=user_id).first() is not None
        )

    return render_template(
        "screens/detail.html",
        recipe=recipe,
        related=related,
        review_form=review_form,
        user_has_reviewed=user_has_reviewed,
        user_has_favourited=user_has_favourited,
    )


@main_bp.route("/recipes/<slug>/review", methods=["POST"])
def post_review(slug):
    if not session.get("logged_in"):
        flash("Please log in to leave a review.", "warning")
        return redirect(url_for("auth.login"))

    recipe = Recipe.query.filter_by(slug=slug, status="published").first_or_404()
    user_id = session.get("user_id")

    existing = Review.query.filter_by(recipe_id=recipe.id, user_id=user_id).first()
    if existing:
        flash("You have already reviewed this recipe.", "warning")
        return redirect(url_for("main.recipe_detail", slug=slug))

    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            recipe_id=recipe.id,
            user_id=user_id,
            rating=int(form.rating.data),
            body=form.body.data.strip(),
            status="approved",
        )
        db.session.add(review)
        db.session.commit()
        flash("Your review has been posted!", "success")
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "danger")

    return redirect(url_for("main.recipe_detail", slug=slug) + "#tab-reviews")


@main_bp.route("/recipes/<slug>/favourite", methods=["POST"])
def toggle_favourite(slug):
    if not session.get("logged_in"):
        flash("Please log in to save favourites.", "warning")
        return redirect(url_for("auth.login"))

    recipe = Recipe.query.filter_by(slug=slug, status="published").first_or_404()
    user_id = session.get("user_id")

    existing = Favourite.query.filter_by(recipe_id=recipe.id, user_id=user_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Removed from favourites.", "info")
    else:
        db.session.add(Favourite(user_id=user_id, recipe_id=recipe.id))
        db.session.commit()
        flash("Added to favourites!", "success")

    return redirect(url_for("main.recipe_detail", slug=slug))


@main_bp.route("/stores")
def stores():
    q = request.args.get("q", "").strip()
    store_query = Store.query
    if q:
        store_query = store_query.filter(
            or_(Store.name.ilike(f"%{q}%"), Store.specialties.ilike(f"%{q}%"))
        )
    stores_list = store_query.order_by(Store.featured.desc(), Store.rating.desc()).all()
    return render_template("screens/stores.html", stores=stores_list)


@main_bp.route("/about")
def about():
    team = [
        {"name": "Damilola Oni",     "initial": "DO", "role": "Backend · Flask routes & DB",                               "avatar_bg": None,   "image": "uploads/avatars/DO.jpeg"},
        {"name": "Ufuoma Akpoguma",  "initial": "UA", "role": "Frontend (Login, Register & About) · Bootstrap & UI/UX",    "avatar_bg": "gold", "image": "uploads/avatars/UA.jpg"},
        {"name": "Peter Orji",       "initial": "PO", "role": "Frontend (Landing & Favourites) · Bootstrap",               "avatar_bg": "red",  "image": "uploads/avatars/PO.jpg"},
    ]
    return render_template("screens/about.html", team=team)

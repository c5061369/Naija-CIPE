from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from db import db
from models import Recipe, Category, User, Review, Store
from forms import RecipeForm, CategoryForm
from slugify import slugify

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin access required.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def _make_slug(title):
    base = slugify(title)
    slug = base
    counter = 1
    while Recipe.query.filter_by(slug=slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


@admin_bp.route("/")
@admin_bp.route("")
@admin_required
def admin_panel():
    active_view = request.args.get("view", "dashboard")
    stats = {
        "recipes": Recipe.query.filter_by(status="published").count(),
        "users": User.query.count(),
        "reviews": Review.query.filter_by(status="approved").count(),
        "pending": Recipe.query.filter_by(status="pending").count(),
    }
    recent_recipes = Recipe.query.order_by(Recipe.created_at.desc()).limit(5).all()
    all_recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
    all_users = User.query.order_by(User.created_at.desc()).all()
    all_reviews = Review.query.order_by(Review.created_at.desc()).all()
    all_categories = Category.query.order_by(Category.name).all()
    category_form = CategoryForm()

    return render_template(
        "screens/admin.html",
        active_view=active_view,
        stats=stats,
        recent_recipes=recent_recipes,
        all_recipes=all_recipes,
        all_users=all_users,
        all_reviews=all_reviews,
        all_categories=all_categories,
        category_form=category_form,
    )


@admin_bp.route("/recipes/add", methods=["GET", "POST"])
@admin_required
def add_recipe():
    form = RecipeForm()
    form.category.choices = [
        (str(c.id), c.name) for c in Category.query.order_by(Category.name).all()
    ]
    if form.validate_on_submit():
        recipe = Recipe(
            title=form.title.data.strip(),
            slug=_make_slug(form.title.data),
            description=form.description.data.strip(),
            category_id=int(form.category.data),
            difficulty=form.difficulty.data,
            prep_time=form.prep_time.data,
            cook_time=form.cook_time.data,
            servings=form.servings.data,
            youtube_url=form.youtube_url.data or None,
            cover_image=form.cover_image.data or None,
            img_class=form.img_class.data,
            status=form.status.data,
            created_by=session["user_id"],
        )
        db.session.add(recipe)
        db.session.flush()
        _save_ingredients(recipe.id, form.ingredients.data)
        _save_instructions(recipe.id, form.instructions.data)
        db.session.commit()
        flash("Recipe published successfully!", "success")
        return redirect(url_for("admin.admin_panel"))

    return render_template("screens/add_recipe.html", form=form, recipe=None)


@admin_bp.route("/recipes/<int:recipe_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    form = RecipeForm(obj=recipe)
    form.category.choices = [
        (str(c.id), c.name) for c in Category.query.order_by(Category.name).all()
    ]

    if request.method == "GET":
        form.category.data = str(recipe.category_id)
        form.ingredients.data = "\n".join(
            f"{i.qty} {i.name}" for i in recipe.ingredient_list
        )
        form.instructions.data = "\n".join(
            s.body for s in recipe.instruction_list
        )

    if form.validate_on_submit():
        recipe.title = form.title.data.strip()
        recipe.description = form.description.data.strip()
        recipe.category_id = int(form.category.data)
        recipe.difficulty = form.difficulty.data
        recipe.prep_time = form.prep_time.data
        recipe.cook_time = form.cook_time.data
        recipe.servings = form.servings.data
        recipe.youtube_url = form.youtube_url.data or None
        recipe.cover_image = form.cover_image.data or None
        recipe.img_class = form.img_class.data
        recipe.status = form.status.data

        for ing in recipe.ingredient_list:
            db.session.delete(ing)
        for ins in recipe.instruction_list:
            db.session.delete(ins)
        db.session.flush()
        _save_ingredients(recipe.id, form.ingredients.data)
        _save_instructions(recipe.id, form.instructions.data)
        db.session.commit()
        flash("Recipe updated successfully.", "success")
        return redirect(url_for("admin.admin_panel"))

    return render_template("screens/add_recipe.html", form=form, recipe=recipe)


@admin_bp.route("/recipes/<int:recipe_id>/delete", methods=["POST"])
@admin_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    flash(f'Recipe "{recipe.title}" deleted.', "success")
    return redirect(url_for("admin.admin_panel", view="recipes"))


@admin_bp.route("/reviews/<int:review_id>/approve", methods=["POST"])
@admin_required
def approve_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.status = "approved"
    db.session.commit()
    flash("Review approved.", "success")
    return redirect(url_for("admin.admin_panel", view="reviews"))


@admin_bp.route("/reviews/<int:review_id>/delete", methods=["POST"])
@admin_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted.", "success")
    return redirect(url_for("admin.admin_panel", view="reviews"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash("Cannot delete admin accounts.", "danger")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"User @{user.username} deleted.", "success")
    return redirect(url_for("admin.admin_panel", view="users"))


@admin_bp.route("/categories", methods=["POST"])
@admin_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        from slugify import slugify as _sl
        name = form.name.data.strip()
        if Category.query.filter_by(name=name).first():
            flash("A category with that name already exists.", "warning")
        else:
            cat = Category(
                name=name,
                slug=_sl(name),
                icon_class=form.icon_class.data.strip(),
                description=form.description.data.strip() if form.description.data else None,
            )
            db.session.add(cat)
            db.session.commit()
            flash(f'Category "{name}" added.', "success")
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
    return redirect(url_for("admin.admin_panel", view="categories"))


@admin_bp.route("/categories/<int:cat_id>/delete", methods=["POST"])
@admin_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.recipes.count() > 0:
        flash("Cannot delete a category that still has recipes.", "warning")
    else:
        db.session.delete(cat)
        db.session.commit()
        flash(f'Category "{cat.name}" deleted.', "success")
    return redirect(url_for("admin.admin_panel", view="categories"))


# ── helpers ──────────────────────────────────────────────────────────────────

def _save_ingredients(recipe_id, raw_text):
    from models import Ingredient
    if not raw_text:
        return
    for i, line in enumerate(raw_text.strip().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        qty = parts[0] if len(parts) > 1 else ""
        name = parts[1] if len(parts) > 1 else parts[0]
        db.session.add(Ingredient(recipe_id=recipe_id, qty=qty, name=name, order_num=i))


def _save_instructions(recipe_id, raw_text):
    from models import Instruction
    if not raw_text:
        return
    for i, line in enumerate(raw_text.strip().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        db.session.add(Instruction(recipe_id=recipe_id, step_num=i, title=f"Step {i}", body=line))

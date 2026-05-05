from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from dotenv import load_dotenv
import os
import re
import types
from models import db, User, Recipe, RecipeIngredient, Review, Favourite
from forms import LoginForm, RegisterForm, ReviewForm, ProfileForm, PasswordForm, RecipeForm, CategoryForm
from config import config_map

load_dotenv()

app = Flask(__name__)
csrf = CSRFProtect(app)

flask_env = os.getenv('FLASK_ENV', 'default')
app.config.from_object(config_map.get(flask_env, config_map['default']))

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        # Add columns introduced after initial schema — safe to run repeatedly
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        if 'recipes' in inspector.get_table_names():
            existing = {c['name'] for c in inspector.get_columns('recipes')}
            new_cols = [
                ('img_class',    "VARCHAR(50)  DEFAULT 'img-egusi'"),
                ('youtube_url',  'VARCHAR(500)'),
                ('instructions', 'TEXT'),
                ('status',       "VARCHAR(20)  DEFAULT 'published'"),
            ]
            for col, defn in new_cols:
                if col not in existing:
                    db.session.execute(text(f'ALTER TABLE recipes ADD COLUMN {col} {defn}'))
            db.session.commit()
    except Exception as e:
        print(f"Note: Could not set up database: {e}")


# ─── Helpers ────────────────────────────────────────────────

CATEGORIES = [
    "Soups & Stews", "Rice Dishes", "Swallow",
    "Snacks", "Drinks", "Breakfast", "Grills & BBQ",
]

CATEGORY_LIST = [{"name": c} for c in CATEGORIES]


def recipe_to_card(r):
    """Convert a Recipe model to the dict expected by the recipe_card macro."""
    return {
        "slug": r.slug,
        "title": r.title,
        "category": r.category or "",
        "time": (r.prep_time or 0) + (r.cook_time or 0),
        "rating": round(r.rating or 0, 1),
        "reviews": r.review_count or 0,
        "difficulty": r.difficulty or "Easy",
        "img_class": r.img_class or "img-egusi",
        "cover_image": r.cover_image or "",
        "label": r.title,
    }


def parse_ingredient(line):
    """Parse 'qty [unit] name' into (qty, name) tuple."""
    units = {
        'cup', 'cups', 'g', 'kg', 'ml', 'l', 'tbsp', 'tsp', 'oz', 'lb',
        'bunch', 'pc', 'pcs', 'handful', 'pinch', 'slice', 'slices',
        'clove', 'cloves', 'can', 'cans', 'medium', 'large', 'small',
    }
    parts = line.strip().split()
    if not parts:
        return "", ""
    if parts[0][0].isdigit() or parts[0][0] in ('½', '¼', '¾'):
        if len(parts) >= 3 and parts[1].lower().rstrip('s') in units:
            return f"{parts[0]} {parts[1]}", ' '.join(parts[2:])
        if len(parts) >= 2 and parts[1].lower() in units:
            return f"{parts[0]} {parts[1]}", ' '.join(parts[2:]) if len(parts) > 2 else ""
        return parts[0], ' '.join(parts[1:])
    return "", line.strip()


def update_recipe_rating(recipe):
    """Recalculate and save a recipe's rating and review_count."""
    reviews = Review.query.filter_by(recipe_id=recipe.id).all()
    recipe.review_count = len(reviews)
    recipe.rating = (sum(r.rating for r in reviews) / len(reviews)) if reviews else 0.0


# ─── Context processors ─────────────────────────────────────
@app.context_processor
def inject_globals():
    current_user = None
    if session.get("logged_in") and session.get("user_id"):
        current_user = User.query.get(session.get("user_id"))
    return {
        "current_year": datetime.now().year,
        "app_name": "NaijaCipe",
        "is_logged_in": session.get("logged_in", False),
        "current_user": current_user,
    }


# ─── Public routes ───────────────────────────────────────────
@app.route("/")
def landing():
    featured = Recipe.query.filter_by(status='published').order_by(
        Recipe.review_count.desc()
    ).limit(4).all()
    featured_recipes = [recipe_to_card(r) for r in featured]

    categories = [
        {"icon": "bi-cup-hot",    "name": "Soups & Stews",  "count": Recipe.query.filter_by(category="Soups & Stews").count()},
        {"icon": "bi-egg-fried",  "name": "Rice Dishes",    "count": Recipe.query.filter_by(category="Rice Dishes").count()},
        {"icon": "bi-basket3",    "name": "Swallow",        "count": Recipe.query.filter_by(category="Swallow").count()},
        {"icon": "bi-cookie",     "name": "Snacks",         "count": Recipe.query.filter_by(category="Snacks").count()},
        {"icon": "bi-cup-straw",  "name": "Drinks",         "count": Recipe.query.filter_by(category="Drinks").count()},
        {"icon": "bi-sunrise",    "name": "Breakfast",      "count": Recipe.query.filter_by(category="Breakfast").count()},
    ]
    return render_template("screens/landing.html", featured_recipes=featured_recipes, categories=categories)


@app.route("/recipes")
def browse():
    sort_by = request.args.get("sort", "popular")
    selected_cats = request.args.getlist("cat")
    selected_diffs = request.args.getlist("diff")
    max_time = request.args.get("time", type=int)
    search_q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 12

    q = Recipe.query.filter_by(status='published')

    if selected_cats:
        q = q.filter(Recipe.category.in_(selected_cats))
    if selected_diffs:
        q = q.filter(Recipe.difficulty.in_(selected_diffs))
    if search_q:
        q = q.filter(Recipe.title.ilike(f"%{search_q}%"))
    if max_time:
        q = q.filter((Recipe.prep_time + Recipe.cook_time) <= max_time)

    if sort_by == "newest":
        q = q.order_by(Recipe.created_at.desc())
    elif sort_by in ("rated", "highest-rated"):
        q = q.order_by(Recipe.rating.desc())
    elif sort_by == "quickest":
        q = q.order_by((Recipe.prep_time + Recipe.cook_time).asc())
    else:
        q = q.order_by(Recipe.review_count.desc())

    paged = q.paginate(page=page, per_page=per_page, error_out=False)
    recipes = [recipe_to_card(r) for r in paged.items]

    return render_template(
        "screens/browse.html",
        recipes=recipes,
        categories=CATEGORY_LIST,
        pagination=paged,
        sort_by=sort_by,
        category=selected_cats[0] if selected_cats else "all",
        total=paged.total,
    )


@app.route("/recipes/<slug>")
def recipe_detail(slug):
    db_recipe = Recipe.query.filter_by(slug=slug).first_or_404()
    review_form = ReviewForm()

    ingredient_list = [
        {"qty": ing.quantity or "", "name": ing.ingredient_name or ""}
        for ing in db_recipe.ingredients
    ]

    steps = [l.strip() for l in (db_recipe.instructions or "").splitlines() if l.strip()]
    instruction_list = [
        {"step_num": i + 1, "title": f"Step {i + 1}", "body": step}
        for i, step in enumerate(steps)
    ]

    review_list = [
        {
            "status": "approved",
            "rating": rv.rating,
            "body": rv.body,
            "created_at": rv.created_at,
            "user": {
                "full_name": rv.author.full_name or rv.author.username,
                "initial": (rv.author.full_name or rv.author.username)[0].upper(),
                "avatar_bg": None,
            },
        }
        for rv in db_recipe.reviews
    ]

    related_db = Recipe.query.filter(
        Recipe.category == db_recipe.category,
        Recipe.id != db_recipe.id,
        Recipe.status == 'published',
    ).limit(3).all()
    related = [
        {
            "slug": r.slug,
            "title": r.title,
            "img_class": r.img_class or "img-egusi",
            "avg_rating": round(r.rating or 0, 1),
            "total_time": (r.prep_time or 0) + (r.cook_time or 0),
        }
        for r in related_db
    ]

    poster_name = "Admin"
    if db_recipe.poster:
        poster_name = db_recipe.poster.full_name or db_recipe.poster.username

    recipe = types.SimpleNamespace(
        id=db_recipe.id,
        slug=db_recipe.slug,
        title=db_recipe.title,
        category=types.SimpleNamespace(name=db_recipe.category or ""),
        img_class=db_recipe.img_class or "img-egusi",
        avg_rating=round(db_recipe.rating or 0, 1),
        review_count=db_recipe.review_count or 0,
        total_time=(db_recipe.prep_time or 0) + (db_recipe.cook_time or 0),
        prep_time=db_recipe.prep_time or 0,
        cook_time=db_recipe.cook_time or 0,
        servings=db_recipe.servings or 0,
        difficulty=db_recipe.difficulty or "",
        description=db_recipe.description or "",
        posted_by=poster_name,
        youtube_url=db_recipe.youtube_url,
        ingredient_list=ingredient_list,
        instruction_list=instruction_list,
        review_list=review_list,
    )

    user_has_favourited = False
    user_has_reviewed = False
    if session.get("logged_in"):
        uid = session["user_id"]
        user_has_favourited = Favourite.query.filter_by(
            user_id=uid, recipe_id=db_recipe.id
        ).first() is not None
        user_has_reviewed = Review.query.filter_by(
            user_id=uid, recipe_id=db_recipe.id
        ).first() is not None

    return render_template(
        "screens/detail.html",
        recipe=recipe,
        user_has_favourited=user_has_favourited,
        user_has_reviewed=user_has_reviewed,
        review_form=review_form,
        related=related,
    )


@app.route("/stores")
def stores():
    stores_list = [
        {"name": "Zaonmart African Food Store", "short_name": "Zaonmart", "rating": 4.8, "featured": True, "verified": True,
         "area": "Sheffield, South Yorkshire", "delivery": "Delivery across the UK",
         "specialties": "Fresh yam, plantain, egusi, ogbono, dried fish, palm oil, scotch bonnets, African food boxes.",
         "tags": ["Fresh produce", "Spices", "Delivery"],
         "website": "https://www.zaonmart.co.uk/", "bg": "linear-gradient(135deg,#0B6E4F,#1C8E6A)"},
        {"name": "Nxtion Food Market", "short_name": "Nxtion", "rating": 4.6, "featured": False, "verified": True,
         "area": "Sheffield", "delivery": "In-store & online",
         "specialties": "Fufu, gari, yam, plantain, grains, seafood, pantry staples, spices & organic produce.",
         "tags": ["Grains", "Seafood", "Online shop"],
         "website": "https://nxtionfoodmarket.com/", "bg": "linear-gradient(135deg,#E3A71C,#B8851A)"},
        {"name": "Alaoma Food Hub", "short_name": "Alaoma", "rating": 4.5, "featured": False, "verified": True,
         "area": "Spital Hill, S4", "delivery": "In-store",
         "specialties": "Nigerian & Ghanaian pantry staples, fresh peppers, egusi, ogbono, smoked fish, plantain.",
         "tags": ["Nigerian staples", "Fresh peppers", "Smoked fish"],
         "website": None, "bg": "linear-gradient(135deg,#D64545,#8E2929)"},
        {"name": "Moor Market — African stalls", "short_name": "Moor Market", "rating": 4.4, "featured": False, "verified": True,
         "area": "The Moor, City Centre", "delivery": "In-store only",
         "specialties": "Multiple vendors: palm oil, yam, plantain, dried peppers, traditional spices, frozen African fish.",
         "tags": ["Multi-vendor", "Central", "Traditional spices"],
         "website": None, "bg": "linear-gradient(135deg,#5A8C3A,#2F5820)"},
        {"name": "Sugarland African Foodstore", "short_name": "Sugarland", "rating": 4.3, "featured": False, "verified": False,
         "area": "Abbeydale Road, S7", "delivery": "In-store",
         "specialties": "Caribbean & West African groceries, scotch bonnets, hard dough bread, plantain, jerk sauces.",
         "tags": ["Caribbean & African", "Plantain", "Hot peppers"],
         "website": None, "bg": "linear-gradient(135deg,#B8691F,#6B3A10)"},
        {"name": "London Road Afro Store", "short_name": "London Road Afro Store", "rating": 4.2, "featured": False, "verified": False,
         "area": "London Road, S2", "delivery": "In-store",
         "specialties": "Yam tubers, plantain, garri, pepper soup spice, locust bean (iru), bitter leaf, snails & periwinkle.",
         "tags": ["Yam tubers", "Bitter leaf", "Iru"],
         "website": None, "bg": "linear-gradient(135deg,#E3A71C,#0B6E4F)"},
    ]
    return render_template("screens/stores.html", stores=stores_list)


@app.route("/about")
def about():
    team = [
        {"name": "Ufuoma Akpoguma", "initial": "D",  "avatar_bg": None},
        {"name": "Damilola Oni",     "initial": "OD", "avatar_bg": "gold"},
        {"name": "Peter Orji",       "initial": "PO", "avatar_bg": "red"},
    ]
    return render_template("screens/about.html", team=team)


# ─── Auth routes ─────────────────────────────────────────────
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        full_name = request.form.get("full_name", "").strip()

        if not username or len(username) < 3:
            flash("Username must be at least 3 characters long.", "danger")
            return render_template("screens/register.html", form=form)
        if not validate_email(email):
            flash("Please enter a valid email address.", "danger")
            return render_template("screens/register.html", form=form)
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("screens/register.html", form=form)
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, "danger")
            return render_template("screens/register.html", form=form)
        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose another.", "danger")
            return render_template("screens/register.html", form=form)
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please use a different email.", "danger")
            return render_template("screens/register.html", form=form)

        try:
            user = User(username=username, email=email, full_name=full_name or username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred during registration: {str(e)}", "danger")
            return render_template("screens/register.html", form=form)

    return render_template("screens/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please provide both username and password.", "danger")
            return render_template("screens/login.html", form=form)

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["logged_in"] = True
            session["user_id"] = user.id
            session["username"] = user.username
            session["is_admin"] = (user.username == "admin")
            flash(f"Welcome back, {user.full_name or user.username}!", "success")
            return redirect(url_for("landing"))
        else:
            flash("Invalid username or password. Please try again.", "danger")

    return render_template("screens/login.html", form=form)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("landing"))


# ─── Authenticated user routes ───────────────────────────────
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in") or not session.get("user_id"):
            session.clear()
            flash("Please log in to view that page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/dashboard")
@login_required
def dashboard():
    uid = session["user_id"]
    db_user = User.query.get(uid)

    fav_count = Favourite.query.filter_by(user_id=uid).count()
    review_count = Review.query.filter_by(user_id=uid).count()

    user = {
        "initial": (db_user.full_name or db_user.username)[0].upper(),
        "full_name": db_user.full_name or db_user.username,
        "created_at": db_user.created_at,
        "avatar_url": db_user.avatar_url,
    }
    stats = {
        "favourites": fav_count,
        "reviews": review_count,
        "recipes_tried": fav_count,
        "streak": 0,
    }

    activity = []
    recent_favs = (
        Favourite.query.filter_by(user_id=uid)
        .order_by(Favourite.created_at.desc()).limit(2).all()
    )
    for fav in recent_favs:
        if fav.recipe:
            activity.append({
                "icon": "bi-heart-fill",
                "icon_bg": "#FFE0E0",
                "icon_color": "var(--naija-red)",
                "text": f"You favourited <strong>{fav.recipe.title}</strong>",
                "date": fav.created_at.strftime("%-d %b %Y"),
                "action_url": url_for("recipe_detail", slug=fav.recipe.slug),
                "action_label": "View",
            })
    recent_reviews = (
        Review.query.filter_by(user_id=uid)
        .order_by(Review.created_at.desc()).limit(2).all()
    )
    for rv in recent_reviews:
        if rv.recipe:
            activity.append({
                "icon": "bi-chat-dots-fill",
                "icon_bg": "#E0F4EC",
                "icon_color": "var(--naija-green)",
                "text": f"You reviewed <strong>{rv.recipe.title}</strong> — gave it {rv.rating} stars",
                "date": rv.created_at.strftime("%-d %b %Y"),
                "action_url": url_for("my_reviews"),
                "action_label": "See",
            })

    return render_template("screens/dashboard.html", user=user, stats=stats, activity=activity)


@app.route("/favourites")
@login_required
def favourites():
    favs = (
        Favourite.query.filter_by(user_id=session["user_id"])
        .order_by(Favourite.created_at.desc()).all()
    )
    fav_recipes = [recipe_to_card(f.recipe) for f in favs if f.recipe]
    return render_template("screens/favourites.html", recipes=fav_recipes)


@app.route("/favourites/toggle/<slug>", methods=["POST"])
@login_required
def toggle_favourite(slug):
    recipe = Recipe.query.filter_by(slug=slug).first_or_404()
    uid = session["user_id"]
    fav = Favourite.query.filter_by(user_id=uid, recipe_id=recipe.id).first()
    if fav:
        db.session.delete(fav)
        flash("Removed from favourites.", "info")
    else:
        db.session.add(Favourite(user_id=uid, recipe_id=recipe.id))
        flash("Saved to favourites!", "success")
    db.session.commit()
    return redirect(url_for("recipe_detail", slug=slug))


@app.route("/reviews/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_user_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != session["user_id"]:
        flash("You can only delete your own reviews.", "danger")
        return redirect(url_for("my_reviews"))
    recipe = review.recipe
    db.session.delete(review)
    db.session.flush()
    update_recipe_rating(recipe)
    db.session.commit()
    flash("Review deleted.", "success")
    return redirect(url_for("my_reviews"))


@app.route("/recipes/<slug>/review", methods=["POST"])
@login_required
def post_review(slug):
    form = ReviewForm()
    recipe = Recipe.query.filter_by(slug=slug).first_or_404()
    if form.validate_on_submit():
        existing = Review.query.filter_by(
            user_id=session["user_id"], recipe_id=recipe.id
        ).first()
        if existing:
            flash("You have already reviewed this recipe.", "warning")
        else:
            review = Review(
                user_id=session["user_id"],
                recipe_id=recipe.id,
                rating=int(form.rating.data),
                body=form.body.data,
            )
            db.session.add(review)
            db.session.flush()
            update_recipe_rating(recipe)
            db.session.commit()
            flash("Your review has been submitted!", "success")
    else:
        flash("Please select a star rating and write a review.", "danger")
    return redirect(url_for("recipe_detail", slug=slug))


@app.route("/my-reviews")
@login_required
def my_reviews():
    db_reviews = (
        Review.query.filter_by(user_id=session["user_id"])
        .order_by(Review.created_at.desc()).all()
    )
    reviews = [
        {
            "id": rv.id,
            "rating": rv.rating,
            "body": rv.body,
            "created_at": rv.created_at,
            "recipe": {
                "slug": rv.recipe.slug,
                "img_class": rv.recipe.img_class or "img-egusi",
                "cover_image": rv.recipe.cover_image or "",
                "title": rv.recipe.title,
                "category": types.SimpleNamespace(name=rv.recipe.category or ""),
            },
        }
        for rv in db_reviews
        if rv.recipe
    ]
    return render_template("screens/my_reviews.html", reviews=reviews)


@app.route("/settings")
@login_required
def user_settings():
    db_user = User.query.get(session["user_id"])
    full_name = db_user.full_name or db_user.username
    user = types.SimpleNamespace(
        initial=full_name[0].upper(),
        full_name=full_name,
        username=db_user.username,
        email=db_user.email,
        avatar_url=db_user.avatar_url,
        location=None,
        bio=None,
        notify_comments=False,
        notify_digest=True,
        notify_new_recipe=False,
        notify_updates=False,
        privacy_show_reviews=True,
        privacy_show_favourites=False,
        privacy_leaderboard=False,
    )
    profile_form = ProfileForm(data={
        "full_name": user.full_name,
        "username": user.username,
        "email": user.email,
    })
    password_form = PasswordForm()
    return render_template(
        "screens/user_settings.html",
        user=user,
        profile_form=profile_form,
        password_form=password_form,
    )


@app.route("/settings/profile", methods=["POST"])
@login_required
def update_profile():
    form = ProfileForm()
    db_user = User.query.get(session["user_id"])
    if form.validate_on_submit():
        new_username = form.username.data
        new_email = form.email.data
        if new_username != db_user.username and User.query.filter_by(username=new_username).first():
            flash("Username already taken.", "danger")
            return redirect(url_for("user_settings"))
        if new_email != db_user.email and User.query.filter_by(email=new_email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("user_settings"))
        db_user.full_name = form.full_name.data
        db_user.username = new_username
        db_user.email = new_email
        db.session.commit()
        session["username"] = db_user.username
        flash("Profile updated.", "success")
    else:
        flash("Please correct the errors in the form.", "danger")
    return redirect(url_for("user_settings"))


@app.route("/settings/password", methods=["POST"])
@login_required
def update_password():
    form = PasswordForm()
    db_user = User.query.get(session["user_id"])
    if form.validate_on_submit():
        if not db_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            db_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Password updated.", "success")
    else:
        flash("Please correct the form errors.", "danger")
    return redirect(url_for("user_settings"))


@app.route("/settings/avatar", methods=["POST"])
@login_required
def upload_avatar():
    file = request.files.get("avatar")
    if not file or file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("user_settings"))
    allowed = {"png", "jpg", "jpeg", "gif", "webp"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        flash("Only PNG, JPG, GIF and WEBP images are allowed.", "danger")
        return redirect(url_for("user_settings"))
    uid = session["user_id"]
    filename = f"{uid}.{ext}"
    save_path = os.path.join(app.root_path, "static", "uploads", "avatars", filename)
    file.save(save_path)
    db_user = User.query.get(uid)
    db_user.avatar_url = f"uploads/avatars/{filename}"
    db.session.commit()
    flash("Profile photo updated.", "success")
    return redirect(url_for("user_settings"))


@app.route("/settings/delete", methods=["POST"])
@login_required
def delete_account():
    db_user = User.query.get(session["user_id"])
    db.session.delete(db_user)
    db.session.commit()
    session.clear()
    flash("Your account has been deleted.", "info")
    return redirect(url_for("landing"))


# ─── Admin routes ────────────────────────────────────────────
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin access required.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/admin")
@admin_required
def admin_panel():
    stats = {
        "recipes": Recipe.query.count(),
        "users": User.query.count(),
        "reviews": Review.query.count(),
        "pending": Recipe.query.filter_by(status='pending').count(),
    }
    recent_recipes = Recipe.query.order_by(Recipe.created_at.desc()).limit(5).all()
    all_recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
    all_users = User.query.order_by(User.created_at.desc()).all()
    all_reviews = Review.query.order_by(Review.created_at.desc()).all()
    all_categories = [
        types.SimpleNamespace(
            name=cat,
            recipe_count=Recipe.query.filter_by(category=cat).count(),
        )
        for cat in CATEGORIES
    ]
    category_form = CategoryForm()
    return render_template(
        "screens/admin.html",
        active_view="dashboard",
        stats=stats,
        recent_recipes=recent_recipes,
        all_recipes=all_recipes,
        all_users=all_users,
        all_reviews=all_reviews,
        all_categories=all_categories,
        category_form=category_form,
    )


@app.route("/admin/add-recipe", methods=["GET", "POST"])
@admin_required
def add_recipe():
    form = RecipeForm()
    form.category.choices = [(c, c) for c in CATEGORIES]

    if form.validate_on_submit():
        base_slug = re.sub(r'[^a-z0-9]+', '-', form.title.data.lower()).strip('-')
        slug = base_slug
        counter = 1
        while Recipe.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        recipe = Recipe(
            title=form.title.data,
            slug=slug,
            category=form.category.data,
            description=form.description.data,
            prep_time=form.prep_time.data,
            cook_time=form.cook_time.data,
            servings=form.servings.data,
            difficulty=form.difficulty.data,
            img_class=form.img_class.data,
            cover_image=form.cover_image.data or None,
            instructions=form.instructions.data,
            youtube_url=form.youtube_url.data or None,
            status=form.status.data,
            posted_by=session["user_id"],
        )
        db.session.add(recipe)
        db.session.flush()

        for line in form.ingredients.data.splitlines():
            line = line.strip()
            if not line:
                continue
            qty, name = parse_ingredient(line)
            db.session.add(RecipeIngredient(
                recipe_id=recipe.id,
                quantity=qty,
                ingredient_name=name,
            ))

        db.session.commit()
        flash("Recipe published successfully!", "success")
        return redirect(url_for("admin_panel"))

    return render_template("screens/add_recipe.html", form=form, recipe=None)


@app.route("/admin/edit-recipe/<int:recipe_id>", methods=["GET", "POST"])
@admin_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    form = RecipeForm()
    form.category.choices = [(c, c) for c in CATEGORIES]

    if form.validate_on_submit():
        recipe.title = form.title.data
        recipe.category = form.category.data
        recipe.description = form.description.data
        recipe.prep_time = form.prep_time.data
        recipe.cook_time = form.cook_time.data
        recipe.servings = form.servings.data
        recipe.difficulty = form.difficulty.data
        recipe.img_class = form.img_class.data
        recipe.cover_image = form.cover_image.data or None
        recipe.instructions = form.instructions.data
        recipe.youtube_url = form.youtube_url.data or None
        recipe.status = form.status.data

        RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
        for line in form.ingredients.data.splitlines():
            line = line.strip()
            if not line:
                continue
            qty, name = parse_ingredient(line)
            db.session.add(RecipeIngredient(
                recipe_id=recipe.id,
                quantity=qty,
                ingredient_name=name,
            ))

        db.session.commit()
        flash("Recipe updated successfully!", "success")
        return redirect(url_for("admin_panel"))

    if request.method == "GET":
        form.title.data = recipe.title
        form.description.data = recipe.description
        form.category.data = recipe.category
        form.difficulty.data = recipe.difficulty
        form.prep_time.data = recipe.prep_time
        form.cook_time.data = recipe.cook_time
        form.servings.data = recipe.servings
        form.ingredients.data = "\n".join(
            f"{ri.quantity} {ri.ingredient_name}".strip()
            for ri in recipe.ingredients
        )
        form.instructions.data = recipe.instructions
        form.youtube_url.data = recipe.youtube_url
        form.img_class.data = recipe.img_class
        form.cover_image.data = recipe.cover_image or ""
        form.status.data = recipe.status

    return render_template("screens/add_recipe.html", form=form, recipe=recipe)


@app.route("/admin/delete-recipe/<int:recipe_id>", methods=["POST"])
@admin_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    title = recipe.title
    db.session.delete(recipe)
    db.session.commit()
    flash(f"Recipe '{title}' deleted.", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.username == "admin":
        flash("Cannot delete the admin account.", "danger")
        return redirect(url_for("admin_panel"))
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' deleted.", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/reviews/<int:review_id>/delete", methods=["POST"])
@admin_required
def admin_delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted.", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/add-category", methods=["POST"])
@admin_required
def add_category():
    flash("Categories are managed in the codebase (CATEGORIES list in app.py).", "info")
    return redirect(url_for("admin_panel"))


@app.route("/admin/delete-category/<int:cat_id>", methods=["POST"])
@admin_required
def delete_category(cat_id):
    flash("Categories are managed in the codebase (CATEGORIES list in app.py).", "info")
    return redirect(url_for("admin_panel"))


# ─── Error handlers ──────────────────────────────────────────
@app.errorhandler(404)
def not_found(_e):
    return render_template("screens/404.html"), 404


@app.errorhandler(500)
def server_error(_e):
    return render_template("screens/404.html"), 500


if __name__ == "__main__":
    app.run(debug=True)

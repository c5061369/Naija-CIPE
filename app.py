from flask import Flask, render_template, redirect, url_for, flash, request, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = "naijacipe-secret-key-change-in-production"


# ─── Context processors ─────────────────────────────────────
@app.context_processor
def inject_globals():
    """Inject variables available in every template."""
    return {
        "current_year": datetime.now().year,
        "app_name": "NaijaCipe",
        "is_logged_in": session.get("logged_in", False),
        "is_admin": session.get("is_admin", False),
        "current_user": session.get("username", None),
    }


# ─── Public routes ───────────────────────────────────────────
@app.route("/")
def landing():
    featured_recipes = [
        {"slug": "jollof-rice",  "title": "Classic Nigerian Jollof Rice", "category": "Rice Dishes",  "time": 45, "rating": 4.9, "difficulty": "Medium", "img_class": "img-jollof",  "label": "Jollof Rice"},
        {"slug": "egusi-soup",   "title": "Egusi Soup with Pounded Yam",  "category": "Soups & Stews","time": 60, "rating": 4.7, "difficulty": "Medium", "img_class": "img-egusi",   "label": "Egusi Soup"},
        {"slug": "suya",         "title": "Spicy Beef Suya Skewers",      "category": "Grills & BBQ", "time": 30, "rating": 4.9, "difficulty": "Easy",   "img_class": "img-suya",    "label": "Suya"},
        {"slug": "chinchin",     "title": "Crunchy Nigerian Chin Chin",   "category": "Snacks",       "time": 50, "rating": 4.3, "difficulty": "Easy",   "img_class": "img-chinchin","label": "Chin Chin"},
    ]
    categories = [
        {"icon": "bi-cup-hot",    "name": "Soups & Stews",  "count": 42},
        {"icon": "bi-egg-fried",  "name": "Rice Dishes",    "count": 28},
        {"icon": "bi-basket3",    "name": "Swallow",        "count": 15},
        {"icon": "bi-cookie",     "name": "Snacks",         "count": 36},
        {"icon": "bi-cup-straw",  "name": "Drinks",         "count": 18},
        {"icon": "bi-sunrise",    "name": "Breakfast",      "count": 24},
    ]
    return render_template("screens/landing.html", featured_recipes=featured_recipes, categories=categories)


@app.route("/recipes")
def browse():
    recipes = [
        {"slug": "jollof-rice",    "title": "Classic Jollof Rice",      "category": "Rice Dishes", "time": 45, "rating": 4.9, "reviews": 128, "difficulty": "Medium", "img_class": "img-jollof",      "label": "Jollof Rice"},
        {"slug": "egusi-soup",     "title": "Egusi Soup",               "category": "Soups",       "time": 60, "rating": 4.7, "reviews": 94,  "difficulty": "Medium", "img_class": "img-egusi",       "label": "Egusi Soup"},
        {"slug": "suya",           "title": "Spicy Beef Suya",          "category": "Grills",      "time": 30, "rating": 4.9, "reviews": 210, "difficulty": "Easy",   "img_class": "img-suya",        "label": "Suya"},
        {"slug": "pepper-soup",    "title": "Catfish Pepper Soup",      "category": "Soups",       "time": 40, "rating": 4.6, "reviews": 72,  "difficulty": "Easy",   "img_class": "img-pepper",      "label": "Pepper Soup"},
        {"slug": "chinchin",       "title": "Crunchy Chin Chin",        "category": "Snacks",      "time": 50, "rating": 4.3, "reviews": 56,  "difficulty": "Easy",   "img_class": "img-chinchin",    "label": "Chin Chin"},
        {"slug": "puff-puff",      "title": "Fluffy Puff Puff",         "category": "Snacks",      "time": 35, "rating": 4.8, "reviews": 183, "difficulty": "Easy",   "img_class": "img-puffpuff",    "label": "Puff Puff"},
        {"slug": "moi-moi",        "title": "Steamed Moi Moi",          "category": "Breakfast",   "time": 75, "rating": 4.5, "reviews": 64,  "difficulty": "Medium", "img_class": "img-moimoi",      "label": "Moi Moi"},
        {"slug": "efo-riro",       "title": "Efo Riro",                 "category": "Soups",       "time": 50, "rating": 4.7, "reviews": 89,  "difficulty": "Medium", "img_class": "img-efo",         "label": "Efo Riro"},
        {"slug": "akara",          "title": "Akara (Bean Cakes)",       "category": "Breakfast",   "time": 30, "rating": 4.6, "reviews": 71,  "difficulty": "Easy",   "img_class": "img-akara",       "label": "Akara"},
        {"slug": "zobo",           "title": "Zobo Hibiscus Drink",      "category": "Drinks",      "time": 25, "rating": 4.4, "reviews": 48,  "difficulty": "Easy",   "img_class": "img-zobo",        "label": "Zobo Drink"},
        {"slug": "banana-bread",   "title": "Banana Nut Bread",         "category": "Snacks",      "time": 70, "rating": 4.2, "reviews": 38,  "difficulty": "Easy",   "img_class": "img-bananabread", "label": "Banana Bread"},
        {"slug": "okra-soup",      "title": "Okra Soup (Draw Soup)",    "category": "Soups",       "time": 45, "rating": 4.5, "reviews": 55,  "difficulty": "Easy",   "img_class": "img-okra",        "label": "Okra Soup"},
    ]
    categories = [
        {"name": "Soups & Stews"}, {"name": "Rice Dishes"}, {"name": "Swallow"},
        {"name": "Snacks"}, {"name": "Drinks"}, {"name": "Breakfast"}, {"name": "Grills"},
    ]
    pagination = {"page": 1, "per_page": 12, "pages": 1, "has_prev": False, "has_next": False,
                  "prev_num": None, "next_num": None}
    sort_by = request.args.get("sort", "popular")
    category = request.args.get("category", "all")
    return render_template("screens/browse.html", recipes=recipes, categories=categories,
                           pagination=pagination, sort_by=sort_by, category=category, total=len(recipes))


@app.route("/recipes/<slug>")
def recipe_detail(slug):
    recipe = {
        "slug": slug,
        "title": "Egusi Soup with Pounded Yam",
        "category": "Soups & Stews",
        "img_class": "img-egusi",
        "rating": 4.7,
        "review_count": 94,
        "time": 60,
        "prep_time": 15,
        "cook_time": 45,
        "servings": 6,
        "difficulty": "Medium",
        "posted_by": "Admin",
        "description": "A rich, velvety soup made from ground melon seeds, leafy greens, assorted meats and fish. Served with pounded yam, it's the centrepiece of countless Nigerian Sunday tables.",
        "ingredients": [
            {"qty": "2 cups",  "name": "Egusi (melon) seeds, ground"},
            {"qty": "500 g",   "name": "Assorted meat (beef, tripe, shaki)"},
            {"qty": "300 g",   "name": "Dried fish or stockfish, soaked"},
            {"qty": "1 cup",   "name": "Palm oil"},
            {"qty": "4 pcs",   "name": "Scotch bonnet peppers, blended"},
            {"qty": "1 bunch", "name": "Ugu (pumpkin) or spinach leaves"},
            {"qty": "2 tbsp",  "name": "Ground crayfish"},
            {"qty": "2 cubes", "name": "Seasoning (Maggi / Knorr)"},
            {"qty": "1 tsp",   "name": "Salt, to taste"},
            {"qty": "2 tbsp",  "name": "Locust beans (Iru) — optional"},
        ],
        "instructions": [
            {"step": 1, "title": "Cook the meats",        "body": "Season assorted meats with onion, salt and a seasoning cube. Boil for 20 minutes until tender. Reserve the stock."},
            {"step": 2, "title": "Prepare the egusi paste","body": "Mix ground egusi with a little water to form a thick paste."},
            {"step": 3, "title": "Fry the base",          "body": "Heat palm oil, add sliced onions, then the egusi paste in lumps. Fry for 10 minutes, stirring occasionally."},
            {"step": 4, "title": "Build the soup",        "body": "Add blended pepper, reserved stock, locust beans and crayfish. Simmer for 15 minutes."},
            {"step": 5, "title": "Finish",                "body": "Stir in cooked meats, dried fish, and finally the ugu leaves. Simmer for 5 more minutes. Taste and adjust seasoning."},
            {"step": 6, "title": "Serve hot",             "body": "Serve with pounded yam, eba or fufu."},
        ],
        "reviews": [
            {"author": "Adaeze O.", "initial": "A", "avatar_bg": None,      "rating": 5, "date": "2 days ago",  "body": "Reminded me of my grandmother's kitchen. Tip: let the egusi fry a little longer than you think — that's where the flavour comes from."},
            {"author": "Tunde B.",  "initial": "T", "avatar_bg": "gold",    "rating": 4, "date": "1 week ago", "body": "Great recipe. I used spinach instead of ugu since I couldn't find it — still delicious."},
            {"author": "Chinwe M.", "initial": "C", "avatar_bg": "red",     "rating": 4, "date": "2 weeks ago","body": "Perfect for my son's birthday — the whole family approved!"},
        ],
        "related": [
            {"slug": "efo-riro",    "title": "Efo Riro",    "img_class": "img-efo",   "rating": 4.7, "time": 50},
            {"slug": "okra-soup",   "title": "Okra Soup",   "img_class": "img-okra",  "rating": 4.5, "time": 45},
            {"slug": "pepper-soup", "title": "Pepper Soup", "img_class": "img-pepper","rating": 4.6, "time": 40},
        ],
    }
    return render_template("screens/detail.html", recipe=recipe)


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
        {"name": "Daniel Akpoguma", "initial": "D", "role": "Backend · Flask routes & DB",        "avatar_bg": None},
        {"name": "Teammate 2",      "initial": "T2","role": "Frontend · Bootstrap & UX",          "avatar_bg": "gold"},
        {"name": "Teammate 3",      "initial": "T3","role": "Testing · PM & Documentation",       "avatar_bg": "red"},
    ]
    return render_template("screens/about.html", team=team)


# ─── Auth routes ─────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Placeholder — connect to DB in production
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("screens/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == "admin" and password == "admin1234":
            session["logged_in"] = True
            session["is_admin"]  = True
            session["username"]  = "admin"
            flash("Logged in as Admin.", "success")
            return redirect(url_for("admin_panel"))
        elif username == "demo_user" and password == "demo1234":
            session["logged_in"] = True
            session["is_admin"]  = False
            session["username"]  = "adaeze_cooks"
            flash("Welcome back, Adaeze!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials. Try demo_user / demo1234.", "danger")
    return render_template("screens/login.html")


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
        if not session.get("logged_in"):
            flash("Please log in to view that page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/dashboard")
@login_required
def dashboard():
    username = session.get("username", "user")
    user = {
        "initial": username[0].upper(),
        "full_name": "Adaeze Cooks" if username == "adaeze_cooks" else username.title(),
        "created_at": datetime(2024, 1, 15),
    }
    stats = {"favourites": 14, "reviews": 8, "recipes_tried": 22, "streak": 3}
    activity = [
        {"icon": "bi-heart-fill",     "icon_bg": "#FFE0E0", "icon_color": "var(--naija-red)",      "text": "You favourited <strong>Classic Jollof Rice</strong>",       "date": "3 days ago",  "action_url": url_for("recipe_detail", slug="jollof-rice"), "action_label": "View"},
        {"icon": "bi-chat-dots-fill", "icon_bg": "#E0F4EC", "icon_color": "var(--naija-green)",    "text": "You reviewed <strong>Egusi Soup</strong> — gave it 5 stars", "date": "5 days ago",  "action_url": url_for("my_reviews"), "action_label": "See"},
        {"icon": "bi-heart-fill",     "icon_bg": "#FFF3D1", "icon_color": "var(--naija-gold-dark)","text": "You favourited <strong>Spicy Beef Suya</strong>",            "date": "1 week ago",  "action_url": url_for("recipe_detail", slug="suya"),        "action_label": "View"},
        {"icon": "bi-chat-dots-fill", "icon_bg": "#E8E4FF", "icon_color": "#6B4FCF",              "text": "You reviewed <strong>Puff Puff</strong> — gave it 4 stars",  "date": "2 weeks ago", "action_url": url_for("my_reviews"), "action_label": "See"},
    ]
    return render_template("screens/dashboard.html", user=user, stats=stats, activity=activity)


@app.route("/favourites")
@login_required
def favourites():
    fav_recipes = [
        {"slug": "jollof-rice", "title": "Classic Jollof Rice",  "category": "Rice Dishes","time": 45, "rating": 4.9, "difficulty": "Medium","img_class": "img-jollof",   "label": "Jollof Rice"},
        {"slug": "egusi-soup",  "title": "Egusi Soup",           "category": "Soups",      "time": 60, "rating": 4.7, "difficulty": "Medium","img_class": "img-egusi",    "label": "Egusi Soup"},
        {"slug": "suya",        "title": "Spicy Beef Suya",      "category": "Grills",     "time": 30, "rating": 4.9, "difficulty": "Easy",  "img_class": "img-suya",     "label": "Suya"},
        {"slug": "puff-puff",   "title": "Fluffy Puff Puff",     "category": "Snacks",     "time": 35, "rating": 4.8, "difficulty": "Easy",  "img_class": "img-puffpuff", "label": "Puff Puff"},
        {"slug": "moi-moi",     "title": "Steamed Moi Moi",      "category": "Breakfast",  "time": 75, "rating": 4.5, "difficulty": "Medium","img_class": "img-moimoi",   "label": "Moi Moi"},
        {"slug": "akara",       "title": "Akara (Bean Cakes)",   "category": "Breakfast",  "time": 30, "rating": 4.6, "difficulty": "Easy",  "img_class": "img-akara",    "label": "Akara"},
        {"slug": "zobo",        "title": "Zobo Hibiscus Drink",  "category": "Drinks",     "time": 25, "rating": 4.4, "difficulty": "Easy",  "img_class": "img-zobo",     "label": "Zobo Drink"},
        {"slug": "chinchin",    "title": "Crunchy Chin Chin",    "category": "Snacks",     "time": 50, "rating": 4.3, "difficulty": "Easy",  "img_class": "img-chinchin", "label": "Chin Chin"},
    ]
    return render_template("screens/favourites.html", recipes=fav_recipes)


@app.route("/my-reviews")
@login_required
def my_reviews():
    reviews = [
        {"recipe_title": "Egusi Soup",       "recipe_category": "Soups & Stews","img_class": "img-egusi",   "slug": "egusi-soup",  "rating": 5, "date": "5 days ago",   "body": "Reminded me of my grandmother's kitchen. Tip: let the egusi fry a little longer than you think — that's where the flavour comes from."},
        {"recipe_title": "Fluffy Puff Puff", "recipe_category": "Snacks",       "img_class": "img-puffpuff","slug": "puff-puff",   "rating": 4, "date": "2 weeks ago",  "body": "Worked on my second attempt. First batch came out dense — the key is letting the dough rise for a full hour."},
        {"recipe_title": "Classic Jollof Rice","recipe_category": "Rice Dishes", "img_class": "img-jollof",  "slug": "jollof-rice", "rating": 5, "date": "3 weeks ago",  "body": "Party Jollof at its finest. I added a bit of smoked turkey for extra depth and the family fought over the last bits of rice at the bottom of the pot."},
        {"recipe_title": "Spicy Beef Suya",  "recipe_category": "Grills & BBQ", "img_class": "img-suya",    "slug": "suya",        "rating": 4, "date": "1 month ago",  "body": "Yaji spice is the secret — don't skip toasting the groundnuts first. Mine came out closer to mallam-level on my third try."},
    ]
    return render_template("screens/my_reviews.html", reviews=reviews)


@app.route("/settings")
@login_required
def user_settings():
    return render_template("screens/user_settings.html")


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
    stats = {"recipes": 214, "users": 5241, "reviews": 1893, "pending": 7}
    return render_template("screens/admin.html", active_view="dashboard", stats=stats)


@app.route("/admin/add-recipe", methods=["GET", "POST"])
@admin_required
def add_recipe():
    if request.method == "POST":
        flash("Recipe published successfully!", "success")
        return redirect(url_for("admin_panel"))
    return render_template("screens/add_recipe.html")


# ─── Error handlers ──────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("screens/404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("screens/404.html"), 500


if __name__ == "__main__":
    app.run(debug=True)

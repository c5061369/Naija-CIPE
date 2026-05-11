from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from db import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    icon_class = db.Column(db.String(50), default="bi-egg-fried")
    description = db.Column(db.Text)

    recipes = db.relationship("Recipe", back_populates="category", lazy="dynamic")

    def __str__(self):
        return self.name

    @property
    def recipe_count(self):
        return self.recipes.filter_by(status="published").count()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("user", "admin"), default="user")
    avatar_bg = db.Column(db.String(20))
    bio = db.Column(db.Text)
    location = db.Column(db.String(150))

    # Notification preferences
    notify_comments = db.Column(db.Boolean, default=True)
    notify_digest = db.Column(db.Boolean, default=True)
    notify_new_recipe = db.Column(db.Boolean, default=False)
    notify_updates = db.Column(db.Boolean, default=False)

    # Privacy preferences
    privacy_show_reviews = db.Column(db.Boolean, default=True)
    privacy_show_favourites = db.Column(db.Boolean, default=False)
    privacy_leaderboard = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipes = db.relationship("Recipe", back_populates="author", lazy="dynamic")
    review_list = db.relationship("Review", back_populates="user", lazy="dynamic")
    favourite_list = db.relationship("Favourite", back_populates="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def initial(self):
        return (self.full_name[0] if self.full_name else self.username[0]).upper()

    @property
    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.username}>"


class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    difficulty = db.Column(db.Enum("Easy", "Medium", "Hard"), default="Medium")
    prep_time = db.Column(db.Integer, default=0)
    cook_time = db.Column(db.Integer, default=0)
    servings = db.Column(db.Integer, default=4)
    youtube_url = db.Column(db.String(500))
    cover_image = db.Column(db.String(500))
    img_class = db.Column(db.String(100), default="img-egusi")
    status = db.Column(db.Enum("draft", "published", "pending"), default="pending")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship("Category", back_populates="recipes")
    author = db.relationship("User", back_populates="recipes")
    ingredient_list = db.relationship(
        "Ingredient", back_populates="recipe", order_by="Ingredient.order_num", cascade="all, delete-orphan"
    )
    instruction_list = db.relationship(
        "Instruction", back_populates="recipe", order_by="Instruction.step_num", cascade="all, delete-orphan"
    )
    review_list = db.relationship("Review", back_populates="recipe", cascade="all, delete-orphan")
    favourite_list = db.relationship("Favourite", back_populates="recipe", cascade="all, delete-orphan")

    @property
    def total_time(self):
        return (self.prep_time or 0) + (self.cook_time or 0)

    @property
    def avg_rating(self):
        approved = [r.rating for r in self.review_list if r.status == "approved"]
        return round(sum(approved) / len(approved), 1) if approved else 0.0

    @property
    def review_count(self):
        return sum(1 for r in self.review_list if r.status == "approved")

    @property
    def label(self):
        words = self.title.split()
        return " ".join(words[:2]) if len(words) > 2 else self.title

    @property
    def posted_by(self):
        return self.author.username if self.author else "Admin"

    def __repr__(self):
        return f"<Recipe {self.slug}>"


class Ingredient(db.Model):
    __tablename__ = "ingredients"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    qty = db.Column(db.String(50))
    name = db.Column(db.String(255), nullable=False)
    order_num = db.Column(db.Integer, default=0)

    recipe = db.relationship("Recipe", back_populates="ingredient_list")


class Instruction(db.Model):
    __tablename__ = "instructions"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    step_num = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255))
    body = db.Column(db.Text, nullable=False)

    recipe = db.relationship("Recipe", back_populates="instruction_list")


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    body = db.Column(db.Text)
    status = db.Column(db.Enum("approved", "pending"), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipe = db.relationship("Recipe", back_populates="review_list")
    user = db.relationship("User", back_populates="review_list")

    __table_args__ = (db.UniqueConstraint("recipe_id", "user_id", name="unique_review"),)


class Favourite(db.Model):
    __tablename__ = "favourites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="favourite_list")
    recipe = db.relationship("Recipe", back_populates="favourite_list")

    __table_args__ = (db.UniqueConstraint("user_id", "recipe_id", name="unique_favourite"),)


class Store(db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    short_name = db.Column(db.String(100))
    area = db.Column(db.String(255))
    delivery = db.Column(db.String(255))
    specialties = db.Column(db.Text)
    rating = db.Column(db.Numeric(3, 1), default=4.0)
    featured = db.Column(db.Boolean, default=False)
    verified = db.Column(db.Boolean, default=False)
    website = db.Column(db.String(500))
    bg = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tags = db.relationship("StoreTag", back_populates="store", cascade="all, delete-orphan")

    def __str__(self):
        return self.name


class StoreTag(db.Model):
    __tablename__ = "store_tags"

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)
    tag = db.Column(db.String(100), nullable=False)

    store = db.relationship("Store", back_populates="tags")

    def __str__(self):
        return self.tag

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, EmailField, TextAreaField,
    SelectField, IntegerField, URLField, BooleanField, HiddenField,
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional,
    NumberRange, URL, Regexp, ValidationError,
)


class LoginForm(FlaskForm):
    username = StringField(
        "Username or email",
        validators=[DataRequired(), Length(max=255)],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me for 30 days")


class RegisterForm(FlaskForm):
    full_name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=2, max=150)],
    )
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=50),
            Regexp(r"^[a-zA-Z0-9_]+$", message="Letters, numbers and underscores only."),
        ],
    )
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    terms = BooleanField(
        "I agree to the Terms and Privacy Policy",
        validators=[DataRequired(message="You must accept the terms to continue.")],
    )


class RecipeForm(FlaskForm):
    title = StringField(
        "Recipe title",
        validators=[DataRequired(), Length(max=255)],
    )
    description = TextAreaField(
        "Short description",
        validators=[DataRequired(), Length(max=1000)],
    )
    category = SelectField("Category", validators=[DataRequired()])
    difficulty = SelectField(
        "Difficulty",
        choices=[("Easy", "Easy"), ("Medium", "Medium"), ("Hard", "Hard")],
        validators=[DataRequired()],
    )
    prep_time = IntegerField(
        "Prep time (min)",
        validators=[DataRequired(), NumberRange(min=1, max=600)],
    )
    cook_time = IntegerField(
        "Cook time (min)",
        validators=[DataRequired(), NumberRange(min=1, max=600)],
    )
    servings = IntegerField(
        "Servings",
        validators=[DataRequired(), NumberRange(min=1, max=100)],
    )
    ingredients = TextAreaField(
        "Ingredients",
        validators=[DataRequired()],
    )
    instructions = TextAreaField(
        "Instructions",
        validators=[DataRequired()],
    )
    youtube_url = StringField(
        "YouTube URL (optional)",
        validators=[Optional(), Length(max=500)],
    )
    cover_image = StringField(
        "Cover image URL",
        validators=[Optional(), Length(max=500)],
    )
    img_class = SelectField(
        "Image style",
        choices=[
            ("img-jollof", "Jollof Rice"),
            ("img-egusi", "Egusi Soup"),
            ("img-suya", "Suya"),
            ("img-pepper", "Pepper Soup"),
            ("img-chinchin", "Chin Chin"),
            ("img-puffpuff", "Puff Puff"),
            ("img-moimoi", "Moi Moi"),
            ("img-efo", "Efo Riro"),
            ("img-akara", "Akara"),
            ("img-zobo", "Zobo"),
            ("img-bananabread", "Banana Bread"),
            ("img-okra", "Okra Soup"),
        ],
        default="img-egusi",
    )
    status = SelectField(
        "Status",
        choices=[
            ("published", "Published"),
            ("draft", "Draft"),
            ("pending", "Pending review"),
        ],
        default="published",
    )


class ReviewForm(FlaskForm):
    rating = HiddenField("Rating", validators=[DataRequired(message="Please select a star rating.")])
    body = TextAreaField(
        "Review",
        validators=[DataRequired(), Length(min=5, max=2000)],
    )

    def validate_rating(self, field):
        try:
            val = int(field.data)
            if val < 1 or val > 5:
                raise ValidationError("Rating must be between 1 and 5.")
        except (ValueError, TypeError):
            raise ValidationError("Invalid rating value.")


class ProfileForm(FlaskForm):
    full_name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=2, max=150)],
    )
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=50),
            Regexp(r"^[a-zA-Z0-9_]+$", message="Letters, numbers and underscores only."),
        ],
    )
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=500)])


class PasswordForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField(
        "New password",
        validators=[DataRequired(), Length(min=8)],
    )
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )


class CategoryForm(FlaskForm):
    name = StringField("Category name", validators=[DataRequired(), Length(max=100)])
    icon_class = StringField(
        "Bootstrap icon class",
        validators=[DataRequired(), Length(max=50)],
        render_kw={"placeholder": "bi-egg-fried"},
    )
    description = TextAreaField("Description", validators=[Optional(), Length(max=500)])

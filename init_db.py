#!/usr/bin/env python
"""Initialize the MySQL database with schema and sample data."""

import os
import sys
from app import app, db
from models import User, Recipe, RecipeIngredient


def init_database():
    try:
        print("Initializing NaijaCipe database...\n")

        with app.app_context():
            print("  Dropping and recreating tables...")
            db.drop_all()
            db.create_all()
            print("  Tables created")

            admin = User(username='admin', email='admin@naijacipe.app', full_name='Admin User')
            admin.set_password('admin1234')

            demo = User(username='adaeze_cooks', email='adaeze@naijacipe.app', full_name='Adaeze Cooks')
            demo.set_password('Demo1234')

            db.session.add_all([admin, demo])
            db.session.flush()

            jollof = Recipe(
                title='Classic Nigerian Jollof Rice',
                slug='jollof-rice',
                category='Rice Dishes',
                description='Party jollof cooked over an open flame for that smoky bottom.',
                prep_time=15, cook_time=45, servings=6,
                difficulty='Medium', img_class='img-jollof',
                status='published', posted_by=admin.id,
                instructions=(
                    "Blend tomatoes, peppers and onion into a smooth paste.\n"
                    "Fry the blended paste in hot oil for 15 minutes until it dries out.\n"
                    "Add stock, seasoning and washed rice. Stir well.\n"
                    "Cover tightly and cook on low heat for 25 minutes.\n"
                    "Allow to steam on very low heat for 5 more minutes then serve."
                ),
            )
            db.session.add(jollof)
            db.session.flush()

            for qty, name in [
                ("3 cups", "long-grain parboiled rice"),
                ("4",      "large tomatoes, blended"),
                ("3",      "scotch bonnet peppers, blended"),
                ("2",      "large onions"),
                ("½ cup",  "vegetable oil"),
                ("2 cups", "chicken stock"),
                ("2",      "seasoning cubes"),
                ("1 tsp",  "salt, to taste"),
            ]:
                db.session.add(RecipeIngredient(recipe_id=jollof.id, quantity=qty, ingredient_name=name))

            egusi = Recipe(
                title='Egusi Soup with Pounded Yam',
                slug='egusi-soup',
                category='Soups & Stews',
                description='A rich, velvety soup made from ground melon seeds, leafy greens and assorted meats.',
                prep_time=15, cook_time=45, servings=6,
                difficulty='Medium', img_class='img-egusi',
                status='published', posted_by=admin.id,
                instructions=(
                    "Season meats and boil with onion and stock cubes for 20 minutes.\n"
                    "Mix ground egusi with a little water to form a thick paste.\n"
                    "Heat palm oil and fry the egusi paste in lumps for 10 minutes.\n"
                    "Add blended pepper, reserved stock, crayfish and locust beans. Simmer 15 minutes.\n"
                    "Stir in cooked meats, dried fish and ugu leaves. Simmer 5 more minutes.\n"
                    "Serve hot with pounded yam or eba."
                ),
            )
            db.session.add(egusi)
            db.session.flush()

            for qty, name in [
                ("2 cups",  "egusi (melon) seeds, ground"),
                ("500 g",   "assorted meat (beef, tripe)"),
                ("1 cup",   "palm oil"),
                ("4",       "scotch bonnet peppers, blended"),
                ("1 bunch", "ugu (pumpkin) leaves"),
                ("2 tbsp",  "ground crayfish"),
                ("2",       "seasoning cubes"),
            ]:
                db.session.add(RecipeIngredient(recipe_id=egusi.id, quantity=qty, ingredient_name=name))

            db.session.commit()
            print("  Sample users and recipes created\n")
            print("Database initialized successfully!")
            print("\nTest credentials:")
            print("  Admin : admin / admin1234")
            print("  User  : adaeze_cooks / Demo1234")
            return True

    except Exception as err:
        print(f"\nError: {err}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)

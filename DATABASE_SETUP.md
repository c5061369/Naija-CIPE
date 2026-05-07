# Database Setup Guide for NaijaCipe

## Prerequisites

- MySQL Server installed and running
- Python 3.7+
- Virtual environment activated

## Setup Steps

### 1. Configure Database Connection

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Then edit `.env` and update the database credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root          # Your MySQL username
DB_PASSWORD=          # Your MySQL password (leave empty if no password)
DB_NAME=naija_cipe
```

### 2. Initialize the Database

Run the initialization script to create all tables and sample data:

```bash
python init_db.py
```

This will:

- Create the `naija_cipe` database
- Create all required tables (users, recipes, reviews, etc.)
- Insert sample admin and demo user accounts

### 3. Test Credentials

After initialization, you can log in with:

**Admin Account:**

- Username: `admin`
- Password: `admin1234`

**Demo Account:**

- Username: `adaeze_cooks`
- Password: `demo1234`

## Security Features

### Password Security

- All passwords are hashed using Werkzeug's `generate_password_hash`
- Passwords are **never** stored in plain text
- Passwords are verified using `check_password_hash` during login

### Registration Validation

- **Username**: 3+ characters, unique
- **Email**: Valid email format, unique
- **Password**:
  - Minimum 8 characters
  - Must contain uppercase letter
  - Must contain number
  - Must match confirmation password

### SQL Injection Prevention

- All queries use SQLAlchemy ORM with parameterized statements
- User input is never directly concatenated into SQL

### Session Security

- Sessions are server-side and tamper-proof
- User ID and authentication status are stored in the session
- Admin users are identified by username "admin"

## Database Structure

### Users Table

- `id` - Primary key
- `username` - Unique, indexed
- `email` - Unique, indexed
- `password` - Hashed password
- `full_name` - User's full name
- `created_at` / `updated_at` - Timestamps

### Related Tables

- **recipes** - Stores recipe information
- **recipe_ingredients** - Stores ingredients for each recipe
- **reviews** - User reviews for recipes
- **favourites** - User's favorite recipes
- **contacts** - Contact form submissions

## Troubleshooting

### Connection Failed

- Ensure MySQL server is running
- Check credentials in `.env`
- Verify MySQL port (default 3306)

### Table Already Exists

- The schema safely handles existing tables
- Run `python init_db.py` again to reset tables

### Password Validation Errors

- Password must be 8+ characters
- Must include uppercase letter (A-Z)
- Must include number (0-9)
- Example: `MyPassword123`

## Running the App

```bash
python app.py
```

The app will automatically create tables if they don't exist, but it's recommended to run `init_db.py` first for proper setup.

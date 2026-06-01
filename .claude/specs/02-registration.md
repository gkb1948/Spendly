# Spec: Registration

## Overview

Registration enables users to create accounts and authenticate with the system. This step implements both user registration (POST /register) and login (POST /login) handlers—essential prerequisites for the expense tracking features in later steps. Users must provide valid credentials that are securely stored before they can access the application.

## Depends on

- Step 1: Database setup (users table with schema, get_db() function, password hashing via werkzeug)

## Routes

- POST /register — Handle user registration form submission — public
- POST /login — Handle user login form submission — public

## Database changes

No new database changes. The users table created in Step 1 is sufficient:
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- name (TEXT NOT NULL)
- email (TEXT NOT NULL UNIQUE)
- password_hash (TEXT NOT NULL)
- created_at (TEXT DEFAULT CURRENT_TIMESTAMP)

## Templates

Modify:
- templates/register.html — Already has form with name, email, password fields; will POST to /register
- templates/login.html — Already has form with email, password fields; will POST to /login
- templates/base.html — May need to add logout link to navbar (depends on Step 3)

## Files to change

- app.py — Add POST /register and POST /login route handlers
- database/db.py — Add helper functions: get_user_by_email(), create_user()

## Files to create

None (templates already exist from initial setup).

## New dependencies

No new dependencies. werkzeug.security is already in requirements.txt and provides password hashing.

## Rules for implementation

- No SQLAlchemy or ORMs — use raw SQL only
- Parameterised queries only (? placeholders, never f-strings in SQL)
- Passwords hashed with werkzeug.security (generate_password_hash, check_password_hash)
- Use CSS variables — never hardcode hex values
- All templates extend base.html
- Always use url_for() for internal links — never hardcode URLs
- One responsibility per route function — fetch data, validate, insert, render/redirect
- Use abort() for HTTP errors (400, 409, etc.), never raw return statements
- Validate on both client-side and server-side — don't trust form input
- Error messages displayed in templates via {% if error %} blocks already present

## Definition of done

- [ ] User can register with valid name (non-empty), email (valid format), and password (minimum 6 characters)
- [ ] Registration rejects duplicate email addresses with 409 Conflict error
- [ ] Passwords are hashed with werkzeug before storage — plaintext never stored
- [ ] Successful registration redirects to login page with success message
- [ ] Registration validation errors display on register.html with specific error messages
- [ ] User can login with registered email and password
- [ ] Login hashes submitted password and compares against stored hash
- [ ] Successful login creates Flask session and redirects to dashboard (or home)
- [ ] Login rejects invalid credentials (user not found or wrong password) with 401 Unauthorized
- [ ] Login validation errors display on login.html
- [ ] Session is destroyed on logout (Step 3 prerequisite check)
- [ ] Database FK constraints work correctly (PRAGMA foreign_keys enforced in get_db())
- [ ] Run tests: pytest passes all registration/login tests
- [ ] Manual test: register a new user, logout, login with that user, verify access

# scripts/create_admin.py
import argparse, sys, getpass
from importlib import import_module

def autodiscover_app_and_db():
    """
    Tries common patterns:
    - from app import app, db, User
    - from app import create_app, db
    and User from app or app.models
    """
    # 1) try direct app
    try:
        mod = import_module("app")
        app = getattr(mod, "app", None)
        db = getattr(mod, "db", None)
        if app is None and hasattr(mod, "create_app"):
            app = mod.create_app()
        if app is None or db is None:
            raise ImportError("No app/db in app module")
        # find User
        User = getattr(mod, "User", None)
        if User is None:
            try:
                models = import_module("app.models")
                User = getattr(models, "User", None)
            except Exception:
                pass
        if User is None:
            raise ImportError("User model not found; put it in app.py or app/models.py")
        return app, db, User
    except Exception as e:
        raise SystemExit(f"[!] Could not auto-discover app/db/User: {e}\n"
                         f"    Adjust imports in scripts/create_admin.py to match your project.")

def set_user_password(user, password):
    # If your model has set_password(), use it
    if hasattr(user, "set_password"):
        user.set_password(password)
        return
    # Else try a common column: password_hash
    try:
        from werkzeug.security import generate_password_hash
        if hasattr(user, "password_hash"):
            user.password_hash = generate_password_hash(password)
            return
        # fallback: plain 'password' column (not recommended, but we hash anyway)
        if hasattr(user, "password"):
            user.password = generate_password_hash(password)
            return
    except Exception:
        pass
    raise RuntimeError("No way to set password found. Add set_password() to your User model.")

def main():
    parser = argparse.ArgumentParser(description="Create or reset an admin user.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", default="admin")
    parser.add_argument("--reset", action="store_true", help="Reset password if user exists")
    args = parser.parse_args()

    app, db, User = autodiscover_app_and_db()

    with app.app_context():
        # ensure tables
        try:
            db.create_all()
        except Exception:
            pass

        # check existence
        q = User.query.filter((getattr(User, "username")==args.username) | (getattr(User, "email")==args.email))
        existing = q.first()

        pw1 = getpass.getpass("New password: ")
        pw2 = getpass.getpass("Confirm password: ")
        if pw1 != pw2:
            sys.exit("[!] Passwords do not match.")

        if existing:
            if not args.reset:
                print("[i] User exists. Use --reset to change password.")
                return
            set_user_password(existing, pw1)
            # set role if exists
            if hasattr(existing, "role"):
                existing.role = args.role
            db.session.commit()
            print("[✓] Existing admin password updated.")
        else:
            user = User()
            # common fields
            if hasattr(user, "username"):
                user.username = args.username
            if hasattr(user, "email"):
                user.email = args.email
            if hasattr(user, "role"):
                user.role = args.role
            set_user_password(user, pw1)
            db.session.add(user)
            db.session.commit()
            print("[✓] Admin user created.")

if __name__ == "__main__":
    main()

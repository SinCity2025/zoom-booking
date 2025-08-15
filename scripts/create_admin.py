# scripts/create_admin.py
import getpass
from app import app, db, User  # يعتمد على أن ملفك اسمه app.py وفيه app, db, User

def main():
    with app.app_context():
        email = input("Admin Email: ").strip().lower()
        name = input("Admin Name: ").strip()

        pw1 = getpass.getpass("New password: ")
        pw2 = getpass.getpass("Confirm password: ")
        if pw1 != pw2:
            print("[!] Passwords do not match.")
            return

        # تأكد من وجود الجداول
        try:
            db.create_all()
        except Exception:
            pass

        existing = User.query.filter_by(email=email).first()
        if existing:
            print("[i] User exists, updating password & admin flag...")
            existing.set_password(pw1)
            existing.is_admin = True
        else:
            print("[i] Creating new admin user...")
            u = User(name=name, email=email, is_admin=True)
            u.set_password(pw1)
            db.session.add(u)

        db.session.commit()
        print("[✓] Admin user saved successfully.")

if __name__ == "__main__":
    main()

import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import text

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- Models ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    owner_name = db.Column(db.String(120), nullable=False)
    owner_email = db.Column(db.String(120), nullable=False)
    is_approved = db.Column(db.Boolean, default=True)
    trainer_name = db.Column(db.String(120), nullable=True)  # جديد

def create_default_admin():
    admin_email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@site.local")
    admin_pass = os.environ.get("DEFAULT_ADMIN_PASS", "Admin#2025")
    existing = User.query.filter_by(email=admin_email).first()
    if not existing:
        u = User(name="المدير", email=admin_email, is_admin=True)
        u.set_password(admin_pass)
        db.session.add(u)
        db.session.commit()

@app.before_request
def init_db_and_columns():
    # تهيئة قاعدة البيانات + إضافة عمود trainer_name إذا كان ناقص (ترقية آمنة)
    db.create_all()
    with db.engine.connect() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(booking)")).fetchall()]
        if "trainer_name" not in cols:
            conn.execute(text("ALTER TABLE booking ADD COLUMN trainer_name VARCHAR(120)"))
    create_default_admin()

# --------------- Security headers for Canvas iframe ---------------
@app.after_request
def set_canvas_headers(resp):
    resp.headers["Content-Security-Policy"] = "frame-ancestors 'self' https://*.instructure.com https://canvas.instructure.com"
    resp.headers["X-Frame-Options"] = "ALLOWALL"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp

@app.route("/health")
def health():
    return {"status": "ok"}

# ---------------- Helpers ----------------
def current_user():
    uid = session.get("uid")
    return User.query.get(uid) if uid else None

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("الرجاء تسجيل الدخول.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            flash("صلاحيات غير كافية.", "danger")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped

# ---------------- Routes ----------------
@app.route("/")
def index():
    return render_template("index.html", user=current_user())

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        pw = request.form.get("password","")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(pw):
            session["uid"] = user.id
            flash("تم تسجيل الدخول بنجاح.", "success")
            return redirect(url_for("admin" if user.is_admin else "dashboard"))
        flash("بيانات الدخول غير صحيحة.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("تم تسجيل الخروج.", "info")
    return redirect(url_for("index"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        if not (name and email and password):
            flash("يرجى تعبئة جميع الحقول.", "warning")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("هذا البريد مسجّل مسبقًا.", "warning")
            return render_template("register.html")
        u = User(name=name, email=email)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash("تم إنشاء الحساب. يمكنك تسجيل الدخول الآن.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/dashboard", methods=["GET","POST"])
@login_required
def dashboard():
    user = current_user()
    if request.method == "POST":
        title = request.form.get("title","").strip()
        date = request.form.get("date","")
        start_time = request.form.get("start_time","")
        end_time = request.form.get("end_time","")
        trainer_name = request.form.get("trainer_name","").strip() or user.name
        if not (title and date and start_time and end_time):
            flash("يرجى إدخال جميع البيانات.", "warning")
        else:
            try:
                start_dt = datetime.fromisoformat(f"{date}T{start_time}")
                end_dt = datetime.fromisoformat(f"{date}T{end_time}")
                if end_dt <= start_dt:
                    raise ValueError("invalid range")
                conflict = Booking.query.filter(Booking.end > start_dt, Booking.start < end_dt).first()
                if conflict:
                    flash("الموعد متعارض مع حجز آخر.", "danger")
                else:
                    b = Booking(
                        title=title,
                        start=start_dt,
                        end=end_dt,
                        owner_name=user.name,
                        owner_email=user.email,
                        is_approved=True,
                        trainer_name=trainer_name
                    )
                    db.session.add(b); db.session.commit()
                    flash("تم إضافة الحجز بنجاح.", "success")
                    return redirect(url_for("dashboard"))
            except Exception:
                flash("صيغة التاريخ/الوقت غير صحيحة.", "danger")
    my_bookings = Booking.query.filter_by(owner_email=user.email).order_by(Booking.start.desc()).all()
    return render_template("dashboard.html", user=user, my_bookings=my_bookings)

@app.route("/admin")
@admin_required
def admin():
    bookings = Booking.query.order_by(Booking.start.desc()).all()
    return render_template("admin.html", user=current_user(), bookings=bookings)

@app.route("/admin/delete/<int:bid>", methods=["POST"])
@admin_required
def admin_delete(bid):
    b = Booking.query.get_or_404(bid)
    db.session.delete(b); db.session.commit()
    flash("تم حذف الحجز.", "info")
    return redirect(url_for("admin"))

@app.route("/api/bookings")
def api_bookings():
    events = [{
        "id": b.id,
        "title": b.title,  # نخلي العنوان اسم الدورة فقط
        "start": b.start.isoformat(),
        "end": b.end.isoformat(),
        "extendedProps": {
            "trainer": b.trainer_name or b.owner_name
        }
    } for b in Booking.query.all()]
    return jsonify(events)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)

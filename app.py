import os
from datetime import datetime
from io import StringIO
import csv

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import text, inspect

# ===== إعدادات أساسية =====
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# ===== اختيار قاعدة البيانات: Postgres (psycopg3) إن وجد، وإلا SQLite =====
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # توحيد السائق إلى psycopg3
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

    # إضافة sslmode=require إذا لم يكن موجودًا (مهم لـ Render)
    if "sslmode=" not in DATABASE_URL:
        sep = "&" if "?" in DATABASE_URL else "?"
        DATABASE_URL = f"{DATABASE_URL}{sep}sslmode=require"

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    # رجوع آمن إلى SQLite محليًا
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ===== النماذج =====
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
    trainer_name = db.Column(db.String(120), nullable=True)  # اسم المدرب

# ===== إنشاء أدمن افتراضي =====
def create_default_admin():
    admin_email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@site.local")
    admin_pass = os.environ.get("DEFAULT_ADMIN_PASS", "Admin#2025")
    existing = User.query.filter_by(email=admin_email).first()
    if not existing:
        u = User(name="المدير", email=admin_email, is_admin=True)
        u.set_password(admin_pass)
        db.session.add(u)
        db.session.commit()

# ===== تهيئة القاعدة (متوافقة مع Postgres/SQLite) =====
@app.before_request
def init_db_and_columns():
    # إنشاء الجداول إن لم تكن موجودة
    db.create_all()

    # فحص أعمدة جدول booking بطريقة محايدة للمحرك
    insp = inspect(db.engine)
    has_table = insp.has_table("booking")
    cols = [c["name"] for c in insp.get_columns("booking")] if has_table else []

    # إضافة trainer_name إن كان ناقص
    if has_table and "trainer_name" not in cols:
        dialect = db.engine.dialect.name  # "postgresql" أو "sqlite"...
        with db.engine.connect() as conn:
            if dialect == "postgresql":
                conn.execute(text(
                    "ALTER TABLE booking ADD COLUMN IF NOT EXISTS trainer_name VARCHAR(120)"
                ))
            else:
                conn.execute(text(
                    "ALTER TABLE booking ADD COLUMN trainer_name VARCHAR(120)"
                ))

    # إنشاء أدمن افتراضي
    create_default_admin()

# ===== رؤوس أمان أساسية (للـ iframe إن احتجته) =====
@app.after_request
def set_canvas_headers(resp):
    resp.headers["Content-Security-Policy"] = "frame-ancestors 'self' https://*.instructure.com https://canvas.instructure.com"
    resp.headers["X-Frame-Options"] = "ALLOWALL"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp

# ===== صحة الخدمة =====
@app.route("/health")
def health():
    return {"status": "ok"}

# ===== Helpers =====
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

# ===== الصفحات =====
@app.route("/")
def index():
    return render_template("index.html", user=current_user())

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
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

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
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

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    user = current_user()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        date = request.form.get("date", "")
        start_time = request.form.get("start_time", "")
        end_time = request.form.get("end_time", "")
        trainer_name = request.form.get("trainer_name", "").strip() or user.name

        if not (title and date and start_time and end_time):
            flash("يرجى إدخال جميع البيانات.", "warning")
        else:
            try:
                start_dt = datetime.fromisoformat(f"{date}T{start_time}")
                end_dt = datetime.fromisoformat(f"{date}T{end_time}")
                if end_dt <= start_dt:
                    raise ValueError("invalid range")

                conflict = Booking.query.filter(
                    Booking.end > start_dt, Booking.start < end_dt
                ).first()
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
                        trainer_name=trainer_name,
                    )
                    db.session.add(b)
                    db.session.commit()
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
    db.session.delete(b)
    db.session.commit()
    flash("تم حذف الحجز.", "info")
    return redirect(url_for("admin"))

# ===== تصدير CSV للنسخ الاحتياطي =====
@app.route("/admin/export_csv")
@admin_required
def export_csv():
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["id", "title", "trainer_name", "start", "end", "owner_name", "owner_email", "is_approved"])
    for b in Booking.query.order_by(Booking.start.asc()).all():
        writer.writerow([
            b.id, b.title, b.trainer_name or "",
            b.start.isoformat(), b.end.isoformat(),
            b.owner_name, b.owner_email, int(b.is_approved)
        ])
    output = si.getvalue().encode("utf-8-sig")
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=bookings.csv"})

# ===== API للتقويم ومعلومات المدرب =====
@app.route("/api/bookings")
def api_bookings():
    events = [{
        "id": b.id,
        "title": b.title,  # اسم الدورة فقط (التفاصيل في tooltip)
        "start": b.start.isoformat(),
        "end": b.end.isoformat(),
        "extendedProps": {"trainer": b.trainer_name or b.owner_name}
    } for b in Booking.query.all()]
    return jsonify(events)

# ===== إدارة المستخدمين (عرض + ترقية/إلغاء/حذف/تعديل اسم) =====
@app.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.id.desc()).all()
    return render_template("admin_users.html", user=current_user(), users=users)

@app.post("/admin/users/<int:uid>/make_admin")
@admin_required
def admin_make_admin(uid):
    u = User.query.get_or_404(uid)
    if u.is_admin:
        flash("المستخدم بالفعل أدمن.", "info")
        return redirect(url_for("admin_users"))
    u.is_admin = True
    db.session.commit()
    flash(f"تم ترقية {u.email} كأدمن.", "success")
    return redirect(url_for("admin_users"))

@app.post("/admin/users/<int:uid>/remove_admin")
@admin_required
def admin_remove_admin(uid):
    u = User.query.get_or_404(uid)
    # حماية: لا تزيل صلاحيات آخر أدمن
    if u.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash("لا يمكن إزالة صلاحيات آخر أدمن.", "warning")
        return redirect(url_for("admin_users"))
    u.is_admin = False
    db.session.commit()
    flash(f"تم إلغاء أدمن عن {u.email}.", "info")
    return redirect(url_for("admin_users"))

@app.post("/admin/users/<int:uid>/delete")
@admin_required
def admin_delete_user(uid):
    me = current_user()
    u = User.query.get_or_404(uid)

    # منع حذف نفسك
    if me.id == u.id:
        flash("لا يمكن حذف حسابك أنت.", "warning")
        return redirect(url_for("admin_users"))

    # منع حذف آخر أدمن
    if u.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash("لا يمكن حذف آخر أدمن في النظام.", "warning")
        return redirect(url_for("admin_users"))

    # (اختياري) حذف حجوزات المستخدم قبل الحذف لتصفية البيانات
    try:
        Booking.query.filter_by(owner_email=u.email).delete()
    except Exception:
        pass

    db.session.delete(u)
    db.session.commit()
    flash("تم حذف المستخدم وسجلّاته المرتبطة.", "info")
    return redirect(url_for("admin_users"))

@app.post("/admin/users/<int:uid>/rename")
@admin_required
def admin_rename_user(uid):
    u = User.query.get_or_404(uid)
    new_name = (request.form.get("name") or "").strip()
    if not new_name:
        flash("الاسم لا يمكن أن يكون فارغًا.", "warning")
        return redirect(url_for("admin_users"))
    if len(new_name) > 120:
        flash("الاسم طويل جدًا.", "warning")
        return redirect(url_for("admin_users"))
    u.name = new_name
    db.session.commit()
    flash("تم تحديث الاسم بنجاح.", "success")
    return redirect(url_for("admin_users"))

# ===== تشغيل محلي =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
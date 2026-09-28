from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
from functools import wraps
from models import db, User, MissingPerson
from face_utils import compare_faces

# =========================
# App Setup
# =========================
app = Flask(__name__)
app.secret_key = "supersecretkey"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# =========================
# Upload Folders
# =========================
MISSING_UPLOAD = os.path.join(BASE_DIR, "static/uploads/missing")
SEARCH_UPLOAD = os.path.join(BASE_DIR, "static/uploads/search")
POLICE_UPLOAD = os.path.join(BASE_DIR, "static/uploads/police")

os.makedirs(MISSING_UPLOAD, exist_ok=True)
os.makedirs(SEARCH_UPLOAD, exist_ok=True)
os.makedirs(POLICE_UPLOAD, exist_ok=True)

# =========================
# Database Setup
# =========================
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.path.join(INSTANCE_DIR, "tracemaster.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# =========================
# Login Required Decorator
# =========================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Login required!", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# =========================
# Home
# =========================
@app.route("/")
def index():
    reports = MissingPerson.query.filter_by(approved=True)\
        .order_by(MissingPerson.id.desc()).limit(12).all()
    return render_template("index.html", reports=reports)

# =========================
# Register
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# =========================
# Login
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session.clear()
            session["user_id"] = user.id
            session["is_admin"] = user.is_admin
            flash("Login successful!", "success")
            return redirect(url_for("index"))

        flash("Invalid credentials!", "danger")

    return render_template("login.html")

# =========================
# Logout
# =========================
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out!", "info")
    return redirect(url_for("index"))

# =========================
# Report Missing Person
# =========================
@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if request.method == "POST":
        name = request.form.get("name")
        photo = request.files.get("photo")
        verification = request.files.get("police_verification")

        if not name or not photo:
            flash("Name and photo required!", "danger")
            return redirect(url_for("report"))

        # Save missing photo
        photo_filename = secure_filename(f"{uuid.uuid4().hex}_{photo.filename}")
        photo.save(os.path.join(MISSING_UPLOAD, photo_filename))

        # Save police verification
        verification_filename = None
        if verification and verification.filename != "":
            verification_filename = secure_filename(f"{uuid.uuid4().hex}_{verification.filename}")
            verification.save(os.path.join(POLICE_UPLOAD, verification_filename))

        new_report = MissingPerson(
            name=name,
            age=request.form.get("age"),
            gender=request.form.get("gender"),
            height=request.form.get("height"),
            weight=request.form.get("weight"),
            marks=request.form.get("marks"),
            location=request.form.get("location"),
            last_seen_date=request.form.get("last_seen_date"),
            last_seen_time=request.form.get("last_seen_time"),
            clothes=request.form.get("clothes"),
            phone=request.form.get("phone"),
            email=request.form.get("email"),
            relationship=request.form.get("relationship"),
            description=request.form.get("description"),
            photo_path=photo_filename,
            police_verification_photo=verification_filename,
            user_id=session["user_id"]
        )

        db.session.add(new_report)
        db.session.commit()

        flash("Report submitted! Waiting for admin approval.", "success")
        return redirect(url_for("my_reports"))

    return render_template("report.html")

# =========================
# My Reports
# =========================
@app.route("/my_reports")
@login_required
def my_reports():
    reports = MissingPerson.query.filter_by(user_id=session["user_id"])\
        .order_by(MissingPerson.id.desc()).all()
    return render_template("my_reports.html", reports=reports)

# =========================
# Delete Report
# =========================
@app.route("/delete/<int:report_id>", methods=["POST"])
@login_required
def delete_report(report_id):
    report = MissingPerson.query.get_or_404(report_id)

    if report.user_id != session["user_id"] and not session.get("is_admin"):
        flash("Not authorized!", "danger")
        return redirect(url_for("index"))

    file_path = os.path.join(MISSING_UPLOAD, report.photo_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(report)
    db.session.commit()
    flash("Report deleted!", "success")

    return redirect(url_for("my_reports"))
# =========================
# Edit Report
# =========================
@app.route("/edit/<int:report_id>", methods=["GET", "POST"])
@login_required
def edit_report(report_id):
    report = MissingPerson.query.get_or_404(report_id)

    # Only owner or admin can edit
    if report.user_id != session["user_id"] and not session.get("is_admin"):
        flash("Not authorized!", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        report.name = request.form.get("name")
        report.age = request.form.get("age")
        report.gender = request.form.get("gender")
        report.height = request.form.get("height")
        report.weight = request.form.get("weight")
        report.marks = request.form.get("marks")
        report.location = request.form.get("location")
        report.last_seen_date = request.form.get("last_seen_date")
        report.last_seen_time = request.form.get("last_seen_time")
        report.clothes = request.form.get("clothes")
        report.phone = request.form.get("phone")
        report.email = request.form.get("email")
        report.relationship = request.form.get("relationship")
        report.description = request.form.get("description")

        db.session.commit()
        flash("Report updated successfully!", "success")
        return redirect(url_for("my_reports"))

    return render_template("edit_report.html", report=report)
# =========================
# Search (Face + Text)
# =========================
@app.route("/search", methods=["GET", "POST"])
def search():
    results = []

    if request.method == "POST":
        name = request.form.get("name")
        location = request.form.get("location")
        photo = request.files.get("photo")

        query = MissingPerson.query.filter_by(approved=True)

        if name:
            query = query.filter(MissingPerson.name.ilike(f"%{name}%"))
        if location:
            query = query.filter(MissingPerson.location.ilike(f"%{location}%"))

        results = query.all()

        # Face match (search across approved people)
        if photo and photo.filename != "":
            filename = secure_filename(f"{uuid.uuid4().hex}_{photo.filename}")
            filepath = os.path.join(SEARCH_UPLOAD, filename)
            photo.save(filepath)

            matched = []
            all_people = MissingPerson.query.filter_by(approved=True).all()

            for person in all_people:
                person_image = os.path.join(MISSING_UPLOAD, person.photo_path)
                result = compare_faces(filepath, person_image)
                if result.get("match"):
                    matched.append(person)

            results = matched

    return render_template("search.html", results=results)

# =========================
# Admin Dashboard
# =========================
@app.route("/admin")
@login_required
def admin_dashboard():
    if not session.get("is_admin"):
        flash("Admins only!", "danger")
        return redirect(url_for("index"))

    reports = MissingPerson.query.order_by(MissingPerson.id.desc()).all()
    return render_template("admin_dashboard.html", reports=reports)

# =========================
# Approve
# =========================
@app.route("/admin/approve/<int:report_id>", methods=["POST"])
@login_required
def approve_report(report_id):
    if not session.get("is_admin"):
        return redirect(url_for("index"))

    report = MissingPerson.query.get_or_404(report_id)
    report.approved = True
    report.rejected = False
    report.rejection_reason = None
    db.session.commit()

    flash("Report approved!", "success")
    return redirect(url_for("admin_dashboard"))

# =========================
# Reject
# =========================
@app.route("/admin/reject/<int:report_id>", methods=["POST"])
@login_required
def reject_report(report_id):
    if not session.get("is_admin"):
        return redirect(url_for("index"))

    report = MissingPerson.query.get_or_404(report_id)
    reason = request.form.get("rejection_reason")

    report.rejected = True
    report.approved = False
    report.rejection_reason = reason
    db.session.commit()

    flash("Report rejected!", "danger")
    return redirect(url_for("admin_dashboard"))

# =========================
# Admin Face Verify
# =========================
@app.route("/admin/verify/<int:report_id>")
@login_required
def admin_verify(report_id):
    if not session.get("is_admin"):
        return jsonify({"error": "Admin only"})

    report = MissingPerson.query.get_or_404(report_id)

    if not report.photo_path or not report.police_verification_photo:
        return jsonify({"error": "Images missing"})

    person_path = os.path.join(MISSING_UPLOAD, report.photo_path)
    police_path = os.path.join(POLICE_UPLOAD, report.police_verification_photo)

    result = compare_faces(person_path, police_path)
    return jsonify(result)

# =========================
# Create Default Admin
# =========================
with app.app_context():
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            password=generate_password_hash("admin123"),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin created → username: admin | password: admin123")

# =========================
# Run
# =========================
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)
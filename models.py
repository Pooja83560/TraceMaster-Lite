from flask_sqlalchemy import SQLAlchemy
# Initialize DB
db = SQLAlchemy()
# =========================
# User Model
# =========================
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # Admin flag
    is_admin = db.Column(db.Boolean, default=False)
    # User Verification
    police_verification_file = db.Column(db.String(300))
    is_verified = db.Column(db.Boolean, default=False)
    # Relationship → one user can create many reports
    reports = db.relationship(
        "MissingPerson",
        backref="user",
        lazy=True,
        cascade="all, delete"
    )
    def __repr__(self):
        return f"<User {self.username}>"
# =========================
# Missing Person Model
# =========================
class MissingPerson(db.Model):
    __tablename__ = "missing_person"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    height = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    marks = db.Column(db.String(200))
    location = db.Column(db.String(200))
    last_seen_date = db.Column(db.String(20))
    last_seen_time = db.Column(db.String(20))
    clothes = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    relationship = db.Column(db.String(120))
    description = db.Column(db.Text)
    # Images
    photo_path = db.Column(db.String(300))
    police_verification_photo = db.Column(db.String(300))
    # Admin approval system
    approved = db.Column(db.Boolean, default=False)
    rejected = db.Column(db.Boolean, default=False)
    rejection_reason = db.Column(db.Text)
    # Foreign key linking to user
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True
    )
    def __repr__(self):
        return f"<MissingPerson {self.name}>"
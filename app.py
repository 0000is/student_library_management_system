from ml.recommendation_model import recommend_books
import os
import re  #  password Verification

print("flask is running from:", os.getcwd())

from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError   

app = Flask(__name__)
app.secret_key = "elib_secret"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "library.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads", "books")

db = SQLAlchemy(app)

# ================= MODELS =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    approved = db.Column(db.Boolean, default=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)  
    filename = db.Column(db.String(200), nullable=False)
    approved = db.Column(db.Boolean, default=False)

# ================= DEFAULT ADMIN =================
def create_default_admin():
    if not User.query.filter_by(role="admin").first():
        admin = User(
            username="admin",
            password=generate_password_hash("Admin@123"),  # stronger default
            role="admin",
            approved=True
        )
        db.session.add(admin)
        db.session.commit()

# ================= AUTH =================
@app.route('/')
def home():
    return render_template('index.html')

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        # ✅ Secure password check
        if user and check_password_hash(user.password, request.form["password"]):
            if not user.approved:
                return "Awaiting admin approval"
            session["user_id"] = user.id
            session["role"] = user.role
            session["username"] = user.username
            return redirect(url_for(f"{user.role}_dashboard"))

        return "Invalid credentials"

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        # ================= PASSWORD VALIDATION =================
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", password):
            return render_template("register.html", error="Password must contain at least one uppercase letter")

        if not re.search(r"[0-9]", password):
            return render_template("register.html", error="Password must contain at least one number")

        if not re.search(r"[!@#$%^&*]", password):
            return render_template("register.html", error="Password must contain at least one special character")

        # ================= HASH PASSWORD =================
        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed_password,
            role=role,
            approved=False
        )

        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("login"))

        except IntegrityError:
            db.session.rollback()
            error = "Username already exists. Please choose another."
            return render_template("register.html", error=error)

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= ADMIN =================
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    users = User.query.filter(User.role != "admin", User.approved == False).all()
    books = Book.query.all()
    return render_template("admin_dashboard.html", users=users, books=books)

@app.route("/approve_user/<int:user_id>")
def approve_user(user_id):
    user = User.query.get(user_id)
    user.approved = True
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/add", methods=["GET", "POST"])
def admin_add_book():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    if request.method == "POST":
        file = request.files["file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        book = Book(
            title=request.form["title"],
            author=request.form["author"],
            category=request.form["category"], 
            filename=filename,
            approved=True
        )
        db.session.add(book)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_add_book.html")

@app.route("/approve_book/<int:book_id>")
def approve_book(book_id):
    book = Book.query.get(book_id)
    book.approved = True
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/delete_book/<int:book_id>")
def delete_book(book_id):
    book = Book.query.get(book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

# ================= TEACHER =================
@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    books = Book.query.filter_by(approved=True).all()
    return render_template("teacher_dashboard.html", books=books)

@app.route("/upload", methods=["GET", "POST"])
def upload_book():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    if request.method == "POST":
        file = request.files["file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        book = Book(
            title=request.form["title"],
            author=request.form["author"],
            category=request.form["category"],
            filename=filename
        )
        db.session.add(book)
        db.session.commit()
        return redirect(url_for("teacher_dashboard"))
    return render_template("upload_book.html")

# ================= STUDENT =================
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    books = Book.query.filter_by(approved=True).all()

    book_data = []
    for book in books:
        book_data.append({
            "title": book.title,
            "author": book.author,
            "filename": book.filename,
            "downloads": 50,
            "author_popularity": 1,
            "category_science": 1
        })

    recommended_books = recommend_books(book_data)

    if not recommended_books and books:
        recommended_books = [{
            "title": books[0].title,
            "author": books[0].author,
            "filename": books[0].filename
        }]

    return render_template(
        "student_dashboard.html",
        books=books,
        recommended_books=recommended_books
    )

# ================= DOWNLOAD =================
@app.route("/download/<filename>")
def download_book(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

# ================= RUN =================
if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    with app.app_context():
        db.create_all()
        create_default_admin()
    app.run(debug=True)
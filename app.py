
import os
import uuid
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from database import (
    init_db,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_all_internships,
    update_profile_picture,
    remove_profile_picture,
    save_student_profile,
    get_student_profile
)
from recommender import recommend_internships


app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "internmatch-ai-development-secret-key"
)

UPLOAD_FOLDER = Path(app.root_path) / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

init_db()


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def valid_image_signature(file):
    file.seek(0)
    signature = file.read(8)
    file.seek(0)

    return (
        signature.startswith(b"\xff\xd8\xff")
        or signature.startswith(b"\x89PNG\r\n\x1a\n")
    )


def delete_old_picture(filename):
    if not filename:
        return

    safe_name = secure_filename(filename)

    if not safe_name:
        return

    file_path = UPLOAD_FOLDER / safe_name

    if file_path.exists() and file_path.is_file():
        file_path.unlink()


@app.context_processor
def inject_user():
    return {
        "logged_in": "user_id" in session,
        "current_user": session.get("user_name")
    }


# HOME PAGE AND INTERNSHIP RECOMMENDATIONS
@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    profile = {}
    submitted = False
    error = None

    if request.method == "POST":
        submitted = True

        user_id = session.get("user_id")

        if user_id:
            saved_profile = get_student_profile(user_id)

            if saved_profile:
                profile = {
                    "qualification": saved_profile.get("qualification", ""),
                    "field": saved_profile.get("branch", ""),
                    "branch": saved_profile.get("branch", ""),
                    "skills": saved_profile.get("skills", ""),
                    "location": saved_profile.get("preferred_location", ""),
                    "preferred_location": saved_profile.get("preferred_location", ""),
                    "interests": saved_profile.get("preferred_domain", ""),
                    "preferred_domain": saved_profile.get("preferred_domain", "")
                }

        if not profile or not any(
            str(value).strip() for value in profile.values() if value
        ):
            profile = {
                "qualification": request.form.get("qualification", "").strip(),
                "field": request.form.get("field", "").strip(),
                "branch": request.form.get("field", "").strip(),
                "skills": request.form.get("skills", "").strip(),
                "location": request.form.get("location", "").strip(),
                "interests": request.form.get("interests", "").strip()
            }

        if not any(profile.values()):
            error = "Please enter or save at least one profile detail."
        else:
            internships = get_all_internships()
            results = recommend_internships(profile, internships)

    return render_template(
        "index.html",
        results=results,
        profile=profile,
        submitted=submitted,
        error=error
    )


# INTERNSHIP DETAILS PAGE
@app.route("/internship/<int:internship_id>")
def internship_detail(internship_id):
    internships = get_all_internships()

    internship = next(
        (
            item for item in internships
            if int(item.get("id", -1)) == internship_id
        ),
        None
    )

    if internship is None:
        return "Internship not found.", 404

    return render_template(
        "internship_detail.html",
        internship=internship
    )


# REGISTRATION
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        if not create_user(name, email, password_hash):
            flash("This email is already registered. Please log in.", "error")
            return render_template("register.html")

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email)

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# STUDENT DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in to access your dashboard.", "error")
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])

    if not user:
        session.clear()
        flash("Please log in again.", "error")
        return redirect(url_for("login"))

    profile = get_student_profile(session["user_id"])

    return render_template(
        "dashboard.html",
        user=user,
        profile=profile
    )


# SAVE OR UPDATE STUDENT PROFILE
@app.route("/save-profile", methods=["POST"])
def save_profile():
    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    profile = {
        "qualification": request.form.get("qualification", "").strip(),
        "college": request.form.get("college", "").strip(),
        "branch": request.form.get("branch", "").strip(),
        "graduation_year": request.form.get("graduation_year", "").strip(),
        "skills": request.form.get("skills", "").strip(),
        "preferred_domain": request.form.get("preferred_domain", "").strip(),
        "preferred_location": request.form.get("preferred_location", "").strip(),
        "internship_type": request.form.get("internship_type", "").strip()
    }

    if not any(profile.values()):
        flash("Please enter at least one profile detail before saving.", "error")
        return redirect(url_for("dashboard"))

    try:
        save_student_profile(session["user_id"], profile)
        flash("Your student profile has been saved successfully!", "success")
    except Exception:
        app.logger.exception("Student profile save failed.")
        flash("Unable to save your profile. Please try again.", "error")

    return redirect(url_for("dashboard"))


# UPLOAD PROFILE PICTURE
@app.route("/update-profile-picture", methods=["POST"])
def update_picture():
    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    file = request.files.get("profile_picture")

    if not file or not file.filename:
        flash("Please select a picture first.", "error")
        return redirect(url_for("dashboard"))

    if not allowed_file(file.filename):
        flash("Only JPG, JPEG and PNG images are allowed.", "error")
        return redirect(url_for("dashboard"))

    if not valid_image_signature(file):
        flash("The selected file is not a valid JPG or PNG image.", "error")
        return redirect(url_for("dashboard"))

    extension = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"

    old_user = get_user_by_id(session["user_id"])
    old_picture = old_user.get("profile_picture") if old_user else None

    try:
        file.save(UPLOAD_FOLDER / filename)
        update_profile_picture(session["user_id"], filename)
        delete_old_picture(old_picture)

        flash("Profile picture uploaded successfully!", "success")

    except Exception:
        new_path = UPLOAD_FOLDER / filename

        if new_path.exists():
            new_path.unlink()

        app.logger.exception("Profile picture upload failed.")
        flash("Unable to upload the picture. Please try again.", "error")

    return redirect(url_for("dashboard"))


# REMOVE PROFILE PICTURE
@app.route("/remove-profile-picture", methods=["POST"])
def remove_picture():
    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])

    if user and user.get("profile_picture"):
        old_picture = user["profile_picture"]

        remove_profile_picture(session["user_id"])
        delete_old_picture(old_picture)

        flash("Profile picture removed successfully.", "success")
    else:
        flash("No profile picture to remove.", "error")

    return redirect(url_for("dashboard"))


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# ABOUT PAGE
@app.route("/about")
def about():
    return render_template("about.html")


# FILE SIZE ERROR
@app.errorhandler(413)
def file_too_large(error):
    flash("Image is too large. Maximum allowed size is 3 MB.", "error")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

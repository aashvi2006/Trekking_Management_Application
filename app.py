from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models.database import db, User, Staff, Trekker, Trek, Booking
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = "your-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trek.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please login first."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register")
def register():

    return render_template("register.html")

@app.route("/register/trekker", methods=["GET", "POST"])
def register_trekker():

    if request.method == "POST":

        username = request.form.get("username").strip()
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register_trekker"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("register_trekker"))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role="trekker"
        )

        db.session.add(user)
        db.session.flush()

        trekker = Trekker(
            user_id=user.id,
            full_name=request.form.get("full_name"),
            age=int(request.form.get("age")),
            gender=request.form.get("gender"),
            phone=request.form.get("phone"),
            emergency_contact=request.form.get("emergency_contact"),
            address=request.form.get("address")
        )

        db.session.add(trekker)

        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register_trekker.html")

@app.route("/register/staff", methods=["GET", "POST"])
def register_staff():

    if request.method == "POST":

        username = request.form.get("username").strip()
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register_staff"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("register_staff"))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role="staff"
        )

        db.session.add(user)
        db.session.flush()

        staff = Staff(
            user_id=user.id,
            full_name=request.form.get("full_name"),
            phone=request.form.get("phone"),
            experience=int(request.form.get("experience"))
        )

        db.session.add(staff)

        db.session.commit()

        flash("Registration successful. Please login as Staff (approval by Admin may be required).", "success")
        return redirect(url_for("login"))

    return render_template("register_staff.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:

        if current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))

        elif current_user.role == "staff":
            return redirect(url_for("staff_dashboard"))

        else:
            return redirect(url_for("user_dashboard"))

    if request.method == "POST":

        identifier = request.form.get("username", "").strip()
        password = request.form.get("password")

        user = User.query.filter_by(username=identifier).first()

        if not user:
            user = User.query.filter_by(email=identifier.lower()).first()

        if user and check_password_hash(user.password_hash, password):

            if user.role == "admin":

                login_user(user)

                flash("Login successful.", "success")

                return redirect(url_for("admin_dashboard"))

            elif user.role == "staff":

                if user.staff is None:
                    flash("Staff profile not found.", "danger")
                    return redirect(url_for("login"))

                if not user.staff.is_approved:
                    flash(
                        "Your account is waiting for Admin approval.",
                        "warning"
                    )
                    return redirect(url_for("login"))

                if user.staff.is_blacklisted:
                    flash(
                        "Your account has been blacklisted.",
                        "danger"
                    )
                    return redirect(url_for("login"))

                login_user(user)

                flash("Login successful.", "success")

                return redirect(url_for("staff_dashboard"))

            elif user.role == "trekker":

                if user.trekker is None:
                    flash("Trekker profile not found.", "danger")
                    return redirect(url_for("login"))

                if user.trekker.is_blacklisted:
                    flash(
                        "Your account has been blacklisted.",
                        "danger"
                    )
                    return redirect(url_for("login"))

                login_user(user)

                flash("Login successful.", "success")

                return redirect(url_for("user_dashboard"))

            else:

                flash("Invalid user role.", "danger")
                return redirect(url_for("login"))

        flash("Invalid username/email or password.", "danger")

    return render_template("login.html")

@app.route("/admin_dashboard")
@login_required
def admin_dashboard():

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    total_treks = Trek.query.count()

    total_staff = Staff.query.count()

    total_trekkers = Trekker.query.count()

    total_bookings = Booking.query.count()

    return render_template(
        "admin_dashboard.html",
        total_treks=total_treks,
        total_staff=total_staff,
        total_trekkers=total_trekkers,
        total_bookings=total_bookings
    )

@app.route("/staff/dashboard")
@login_required
def staff_dashboard():

    if current_user.role != "staff":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    staff = current_user.staff

    if not staff.is_approved:
        flash("Your account is waiting for Admin approval.", "warning")
        logout_user()
        return redirect(url_for("login"))

    if staff.is_blacklisted:
        flash("Your account has been blacklisted.", "danger")
        logout_user()
        return redirect(url_for("login"))

    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=staff.user_id
    ).all()

    assigned_trek_ids = [trek.id for trek in assigned_treks]

    if assigned_trek_ids:

        participant_count = Booking.query.filter(
            Booking.trek_id.in_(assigned_trek_ids),
            Booking.booking_status == "Booked"
        ).count()

    else:

        participant_count = 0

    active_treks = Trek.query.filter(
        Trek.assigned_staff_id == staff.user_id,
        Trek.status == "Open"
    ).count()

    return render_template(
        "staff_dashboard.html",
        assigned_treks=assigned_treks,
        participant_count=participant_count,
        active_treks=active_treks
    )

@app.route("/user/dashboard")
@login_required
def user_dashboard():

    if current_user.role != "trekker":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    trekker = current_user.trekker

    if trekker.is_blacklisted:
        flash("Your account has been blacklisted.", "danger")
        logout_user()
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    location = request.args.get("location", "").strip()

    query = Trek.query.filter(
        Trek.status == "Open",
        Trek.available_slots > 0
    )

    if search:

        query = query.filter(
            db.or_(
                Trek.trek_name.ilike(f"%{search}%"),
                Trek.location.ilike(f"%{search}%")
            )
        )

    if difficulty:

        query = query.filter(
            Trek.difficulty == difficulty
        )

    if location:

        query = query.filter(
            Trek.location.ilike(f"%{location}%")
        )

    available_treks = query.all()

    bookings = Booking.query.filter_by(
        trekker_id=trekker.user_id
    ).all()

    return render_template(
        "user_dashboard.html",
        available_treks=available_treks,
        bookings=bookings,
        search=search,
        difficulty=difficulty,
        location=location
    )

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully.", "success")

    return redirect(url_for("login"))

@app.route("/admin/manage_treks")
@login_required
def manage_treks():

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()

    if search:

        treks = Trek.query.filter(
            db.or_(
                Trek.trek_name.ilike(f"%{search}%"),
                Trek.location.ilike(f"%{search}%"),
                Trek.difficulty.ilike(f"%{search}%"),
                Trek.status.ilike(f"%{search}%")
            )
        ).all()

    else:

        treks = Trek.query.all()

    return render_template(
        "manage_treks.html",
        treks=treks,
        search=search
    )

@app.route("/admin/add_trek", methods=["GET", "POST"])
@login_required
def add_trek():

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    staff_members = Staff.query.filter_by(
        is_approved=True,
        is_blacklisted=False
    ).all()

    if request.method == "POST":

        start_date_raw = request.form.get("start_date")
        end_date_raw = request.form.get("end_date")

        try:
            start_date = datetime.strptime(start_date_raw, "%Y-%m-%dT%H:%M")
            end_date = datetime.strptime(end_date_raw, "%Y-%m-%dT%H:%M")

        except (TypeError, ValueError):
            flash("Please provide valid start and end dates.", "danger")
            return redirect(url_for("add_trek"))

        if end_date <= start_date:
            flash("End date must be after the start date.", "danger")
            return redirect(url_for("add_trek"))

        trek = Trek(

            trek_name=request.form.get("trek_name"),

            location=request.form.get("location"),

            description=request.form.get("description"),

            difficulty=request.form.get("difficulty"),

            duration=int(request.form.get("duration")),

            total_slots=int(request.form.get("total_slots")),

            available_slots=int(request.form.get("total_slots")),

            start_date=start_date,

            end_date=end_date,

            status=request.form.get("status"),

            assigned_staff_id=request.form.get("assigned_staff_id") or None

        )

        db.session.add(trek)

        db.session.commit()

        flash("Trek Added Successfully.", "success")

        return redirect(url_for("manage_treks"))

    return render_template(
        "add_trek.html",
        staff_members=staff_members
    )

@app.route("/admin/edit_trek/<int:trek_id>", methods=["GET", "POST"])
@login_required
def edit_trek(trek_id):

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    trek = Trek.query.get_or_404(trek_id)

    staff_members = Staff.query.filter_by(
        is_approved=True,
        is_blacklisted=False
    ).all()

    if request.method == "POST":

        start_date_raw = request.form.get("start_date")
        end_date_raw = request.form.get("end_date")

        try:
            start_date = datetime.strptime(start_date_raw, "%Y-%m-%dT%H:%M")
            end_date = datetime.strptime(end_date_raw, "%Y-%m-%dT%H:%M")

        except (TypeError, ValueError):
            flash("Please provide valid start and end dates.", "danger")
            return redirect(url_for("edit_trek", trek_id=trek_id))

        if end_date <= start_date:
            flash("End date must be after the start date.", "danger")
            return redirect(url_for("edit_trek", trek_id=trek_id))

        trek.trek_name = request.form.get("trek_name")
        trek.location = request.form.get("location")
        trek.description = request.form.get("description")
        trek.difficulty = request.form.get("difficulty")
        trek.duration = int(request.form.get("duration"))
        trek.total_slots = int(request.form.get("total_slots"))
        trek.start_date = start_date
        trek.end_date = end_date
        trek.status = request.form.get("status")

        trek.assigned_staff_id = (
            request.form.get("assigned_staff_id")
            if request.form.get("assigned_staff_id")
            else None
        )

        db.session.commit()

        flash("Trek Updated Successfully.", "success")

        return redirect(url_for("manage_treks"))

    return render_template(
        "edit_trek.html",
        trek=trek,
        staff_members=staff_members
    )

@app.route("/admin/delete_trek/<int:trek_id>")
@login_required
def delete_trek(trek_id):

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    trek = Trek.query.get_or_404(trek_id)

    db.session.delete(trek)
    db.session.commit()

    flash("Trek Deleted Successfully.", "success")

    return redirect(url_for("manage_treks"))

@app.route("/admin/manage_staff")
@login_required
def manage_staff():

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()

    query = Staff.query.join(User)

    if search:

        query = query.filter(
            db.or_(
                Staff.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                Staff.phone.ilike(f"%{search}%")
            )
        )

    staff_members = query.all()

    return render_template(
        "manage_staff.html",
        staff_members=staff_members,
        search=search
    )
@app.route("/admin/approve_staff/<int:user_id>")
@login_required
def approve_staff(user_id):

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    staff = Staff.query.filter_by(user_id=user_id).first_or_404()

    if staff.is_approved:
        flash("Staff member is already approved.", "warning")
    else:
        staff.is_approved = True
        db.session.commit()
        flash("Staff approved successfully.", "success")

    return redirect(url_for("manage_staff"))

@app.route("/admin/toggle_staff_blacklist/<int:user_id>")
@login_required
def toggle_staff_blacklist(user_id):

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    staff = Staff.query.filter_by(user_id=user_id).first_or_404()

    if staff.is_blacklisted:

        staff.is_blacklisted = False

        flash(
            f"{staff.full_name} has been removed from blacklist.",
            "success"
        )

    else:

        staff.is_blacklisted = True

        flash(
            f"{staff.full_name} has been blacklisted.",
            "warning"
        )

    db.session.commit()

    return redirect(url_for("manage_staff"))

@app.route("/admin/manage_trekkers")
@login_required
def manage_trekkers():

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()

    query = Trekker.query.join(User)

    if search:

        query = query.filter(
            db.or_(
                Trekker.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                Trekker.phone.ilike(f"%{search}%"),
                Trekker.gender.ilike(f"%{search}%")
            )
        )

    trekkers = query.all()

    return render_template(
        "manage_trekkers.html",
        trekkers=trekkers,
        search=search
    )

@app.route("/admin/toggle_trekker_blacklist/<int:user_id>")
@login_required
def toggle_trekker_blacklist(user_id):

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    trekker = Trekker.query.filter_by(user_id=user_id).first_or_404()

    if trekker.is_blacklisted:

        trekker.is_blacklisted = False

        flash(
            f"{trekker.full_name} has been removed from blacklist.",
            "success"
        )

    else:

        trekker.is_blacklisted = True

        flash(
            f"{trekker.full_name} has been blacklisted.",
            "warning"
        )

    db.session.commit()

    return redirect(url_for("manage_trekkers"))

@app.route("/admin/edit_staff/<int:user_id>", methods=["GET", "POST"])
@login_required
def edit_staff(user_id):

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    staff = Staff.query.filter_by(user_id=user_id).first_or_404()
    user = staff.user

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        experience = request.form.get("experience", "").strip()

        if not username or not email or not full_name or not phone or not experience:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("edit_staff", user_id=user_id))

        duplicate_username = User.query.filter(
            User.username == username,
            User.id != user.id
        ).first()

        if duplicate_username:
            flash("Username already exists.", "danger")
            return redirect(url_for("edit_staff", user_id=user_id))

        duplicate_email = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if duplicate_email:
            flash("Email already exists.", "danger")
            return redirect(url_for("edit_staff", user_id=user_id))

        try:
            experience = int(experience)

            if experience < 0:
                flash("Experience cannot be negative.", "danger")
                return redirect(url_for("edit_staff", user_id=user_id))

        except ValueError:
            flash("Experience must be a valid number.", "danger")
            return redirect(url_for("edit_staff", user_id=user_id))

        # Only fields the admin actually filled in are applied.
        # Password is left untouched unless a new one is provided.
        user.username = username
        user.email = email

        if password:
            user.password_hash = generate_password_hash(password)

        staff.full_name = full_name
        staff.phone = phone
        staff.experience = experience

        db.session.commit()

        flash("Staff details updated successfully.", "success")

        return redirect(url_for("manage_staff"))

    return render_template(
        "edit_staff.html",
        staff=staff
    )

@app.route("/admin/delete_staff/<int:user_id>")
@login_required
def delete_staff(user_id):

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    staff = Staff.query.filter_by(user_id=user_id).first_or_404()
    user = staff.user
    full_name = staff.full_name

    # Unassign this staff member from any treks rather than
    # deleting the treks themselves.
    Trek.query.filter_by(assigned_staff_id=staff.user_id).update(
        {"assigned_staff_id": None}
    )

    db.session.delete(staff)
    db.session.delete(user)
    db.session.commit()

    flash(f"{full_name} has been deleted.", "success")

    return redirect(url_for("manage_staff"))

@app.route("/admin/edit_trekker/<int:user_id>", methods=["GET", "POST"])
@login_required
def edit_trekker(user_id):

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    trekker = Trekker.query.filter_by(user_id=user_id).first_or_404()
    user = trekker.user

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        phone = request.form.get("phone", "").strip()
        emergency_contact = request.form.get("emergency_contact", "").strip()
        address = request.form.get("address", "").strip()

        if not username or not email or not full_name or not age or not phone or not emergency_contact:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("edit_trekker", user_id=user_id))

        duplicate_username = User.query.filter(
            User.username == username,
            User.id != user.id
        ).first()

        if duplicate_username:
            flash("Username already exists.", "danger")
            return redirect(url_for("edit_trekker", user_id=user_id))

        duplicate_email = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if duplicate_email:
            flash("Email already exists.", "danger")
            return redirect(url_for("edit_trekker", user_id=user_id))

        try:
            age = int(age)

            if age <= 0:
                flash("Age must be greater than 0.", "danger")
                return redirect(url_for("edit_trekker", user_id=user_id))

        except ValueError:
            flash("Age must be a valid number.", "danger")
            return redirect(url_for("edit_trekker", user_id=user_id))

        # Only fields the admin actually filled in are applied.
        # Password is left untouched unless a new one is provided.
        user.username = username
        user.email = email

        if password:
            user.password_hash = generate_password_hash(password)

        trekker.full_name = full_name
        trekker.age = age
        trekker.gender = gender
        trekker.phone = phone
        trekker.emergency_contact = emergency_contact
        trekker.address = address

        db.session.commit()

        flash("Trekker details updated successfully.", "success")

        return redirect(url_for("manage_trekkers"))

    return render_template(
        "edit_trekker.html",
        trekker=trekker
    )

@app.route("/admin/delete_trekker/<int:user_id>")
@login_required
def delete_trekker(user_id):

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    trekker = Trekker.query.filter_by(user_id=user_id).first_or_404()
    user = trekker.user
    full_name = trekker.full_name

    # Remove this trekker's bookings along with their account.
    Booking.query.filter_by(trekker_id=trekker.user_id).delete()

    db.session.delete(trekker)
    db.session.delete(user)
    db.session.commit()

    flash(f"{full_name} has been deleted.", "success")

    return redirect(url_for("manage_trekkers"))

@app.route("/admin/bookings")
@login_required
def admin_bookings():

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    bookings = Booking.query.all()

    return render_template(
        "admin_bookings.html",
        bookings=bookings
    )

@app.route("/admin/trek_history")
@login_required
def admin_trek_history():

    if current_user.role != "admin":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    completed_bookings = Booking.query.filter_by(
        booking_status="Completed"
    ).order_by(
        Booking.completed_date.desc()
    ).all()

    return render_template(
        "admin_trek_history.html",
        completed_bookings=completed_bookings
    )

@app.route("/staff/profile", methods=["GET", "POST"])
@login_required
def staff_profile():

    if current_user.role != "staff":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    if not current_user.staff.is_approved:
        flash("Your account is waiting for Admin approval.", "warning")
        logout_user()
        return redirect(url_for("login"))

    if current_user.staff.is_blacklisted:
        flash("Your account has been blacklisted.", "danger")
        logout_user()
        return redirect(url_for("login"))

    staff = current_user.staff

    if request.method == "POST":

        full_name = request.form.get("full_name").strip()
        phone = request.form.get("phone").strip()
        experience = request.form.get("experience")

        if not full_name or not phone or not experience:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("staff_profile"))

        try:
            experience = int(experience)

            if experience < 0:
                flash("Experience cannot be negative.", "danger")
                return redirect(url_for("staff_profile"))

        except ValueError:
            flash("Experience must be a valid number.", "danger")
            return redirect(url_for("staff_profile"))

        staff.full_name = full_name
        staff.phone = phone
        staff.experience = experience

        db.session.commit()

        flash("Profile updated successfully.", "success")

        return redirect(url_for("staff_profile"))

    return render_template(
        "staff_profile.html",
        staff=staff
    )

@app.route("/staff/assigned_treks")
@login_required
def staff_assigned_treks():

    if current_user.role != "staff":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    staff = current_user.staff

    if not staff.is_approved:
        flash("Your account is waiting for Admin approval.", "warning")
        logout_user()
        return redirect(url_for("login"))

    if staff.is_blacklisted:
        flash("Your account has been blacklisted.", "danger")
        logout_user()
        return redirect(url_for("login"))

    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=staff.user_id
    ).all()

    return render_template(
        "staff_assigned_treks.html",
        assigned_treks=assigned_treks
    )

@app.route("/staff/manage_trek/<int:trek_id>", methods=["GET", "POST"])
@login_required
def staff_manage_trek(trek_id):

    if current_user.role != "staff":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    staff = current_user.staff

    if not staff.is_approved:
        flash("Your account is waiting for Admin approval.", "warning")
        logout_user()
        return redirect(url_for("login"))

    if staff.is_blacklisted:
        flash("Your account has been blacklisted.", "danger")
        logout_user()
        return redirect(url_for("login"))

    trek = Trek.query.filter_by(
        id=trek_id,
        assigned_staff_id=staff.user_id
    ).first()

    if trek is None:
        flash("You do not have access to this trek.", "danger")
        return redirect(url_for("staff_assigned_treks"))

    if request.method == "POST":

        try:
            available_slots = int(
                request.form.get("available_slots")
            )
        except (TypeError, ValueError):

            flash(
                "Available slots must be a valid number.",
                "danger"
            )

            return redirect(
                url_for("staff_manage_trek", trek_id=trek.id)
            )

        if available_slots < 0:

            flash(
                "Available slots cannot be negative.",
                "danger"
            )

            return redirect(
                url_for("staff_manage_trek", trek_id=trek.id)
            )

        if available_slots > trek.total_slots:

            flash(
                "Available slots cannot exceed total slots.",
                "danger"
            )

            return redirect(
                url_for("staff_manage_trek", trek_id=trek.id)
            )

        status = request.form.get("status")

        allowed_statuses = [
            "Pending",
            "Approved",
            "Open",
            "Closed",
            "Ongoing",
            "Completed"
        ]

        if status not in allowed_statuses:

            flash(
                "Invalid trek status.",
                "danger"
            )

            return redirect(
                url_for("staff_manage_trek", trek_id=trek.id)
            )

        if trek.status == "Completed" and status != "Completed":

            flash(
                "A completed trek cannot be reopened.",
                "danger"
            )

            return redirect(
                url_for("staff_manage_trek", trek_id=trek.id)
            )

        trek.available_slots = available_slots
        trek.status = status

        if status == "Completed":
            bookings = Booking.query.filter_by(
                trek_id=trek.id,
                booking_status="Booked"
            ).all()

            for booking in bookings:

                booking.booking_status = "Completed"
                booking.completed_date = datetime.utcnow()

        db.session.commit()

        flash(
            "Trek updated successfully.",
            "success"
        )

        return redirect(
            url_for("staff_manage_trek", trek_id=trek.id)
        )

    return render_template(
        "staff_manage_trek.html",
        trek=trek
    )

@app.route("/staff/trek/<int:trek_id>/participants")
@login_required
def staff_trek_participants(trek_id):

    if current_user.role != "staff":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    staff = current_user.staff

    if not staff.is_approved:
        flash("Your account is waiting for Admin approval.", "warning")
        logout_user()
        return redirect(url_for("login"))

    if staff.is_blacklisted:
        flash("Your account has been blacklisted.", "danger")
        logout_user()
        return redirect(url_for("login"))

    trek = Trek.query.filter_by(
        id=trek_id,
        assigned_staff_id=staff.user_id
    ).first()

    if trek is None:
        flash("You do not have access to this trek.", "danger")
        return redirect(url_for("staff_assigned_treks"))

    bookings = Booking.query.filter_by(
        trek_id=trek.id
    ).all()

    return render_template(
        "staff_trek_participants.html",
        trek=trek,
        bookings=bookings
    )

@app.route(
    "/staff/trek/<int:trek_id>/participant/<int:booking_id>/status",
    methods=["POST"]
)
@login_required
def staff_update_participant_status(trek_id, booking_id):

    if current_user.role != "staff":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    staff = current_user.staff

    if not staff.is_approved:
        flash("Your account is waiting for Admin approval.", "warning")
        logout_user()
        return redirect(url_for("login"))

    if staff.is_blacklisted:
        flash("Your account has been blacklisted.", "danger")
        logout_user()
        return redirect(url_for("login"))

    trek = Trek.query.filter_by(
        id=trek_id,
        assigned_staff_id=staff.user_id
    ).first()

    if trek is None:
        flash("You do not have access to this trek.", "danger")
        return redirect(url_for("staff_assigned_treks"))

    booking = Booking.query.filter_by(
        id=booking_id,
        trek_id=trek.id
    ).first()

    if booking is None:
        flash("Participant record not found.", "danger")
        return redirect(
            url_for(
                "staff_trek_participants",
                trek_id=trek.id
            )
        )

    new_status = request.form.get("booking_status")

    allowed_statuses = [
        "Booked",
        "Cancelled",
        "Completed"
    ]

    if new_status not in allowed_statuses:
        flash("Invalid booking status.", "danger")
        return redirect(
            url_for(
                "staff_trek_participants",
                trek_id=trek.id
            )
        )

    old_status = booking.booking_status

    if old_status == new_status:
        flash(
            "Booking status is already set to this value.",
            "info"
        )
        return redirect(
            url_for(
                "staff_trek_participants",
                trek_id=trek.id
            )
        )

    if old_status == "Completed":
        flash(
            "A completed booking cannot be changed.",
            "danger"
        )
        return redirect(
            url_for(
                "staff_trek_participants",
                trek_id=trek.id
            )
        )

    if old_status == "Booked" and new_status == "Cancelled":

        if trek.available_slots < trek.total_slots:
            trek.available_slots += 1

        booking.completed_date = None

    elif old_status == "Cancelled" and new_status == "Booked":

        if trek.status != "Open":
            flash(
                "A cancelled booking can only be restored "
                "while the trek is Open.",
                "danger"
            )
            return redirect(
                url_for(
                    "staff_trek_participants",
                    trek_id=trek.id
                )
            )

        if trek.available_slots <= 0:
            flash(
                "There are no available slots for this trek.",
                "danger"
            )
            return redirect(
                url_for(
                    "staff_trek_participants",
                    trek_id=trek.id
                )
            )

        trek.available_slots -= 1

        booking.completed_date = None

    elif old_status == "Booked" and new_status == "Completed":

        booking.completed_date = datetime.utcnow()

    booking.booking_status = new_status

    db.session.commit()

    flash(
        "Participant booking status updated successfully.",
        "success"
    )

    return redirect(
        url_for(
            "staff_trek_participants",
            trek_id=trek.id
        )
    )

@app.route("/user/profile", methods=["GET", "POST"])
@login_required
def user_profile():

    if current_user.role != "trekker":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    trekker = current_user.trekker

    if trekker.is_blacklisted:
        flash("Your account has been blacklisted.", "danger")
        logout_user()
        return redirect(url_for("login"))

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        age = request.form.get("age")
        gender = request.form.get("gender", "").strip()

        if not full_name or not phone or not age or not gender:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("user_profile"))

        try:
            age = int(age)

            if age <= 0:
                flash("Age must be greater than 0.", "danger")
                return redirect(url_for("user_profile"))

        except ValueError:

            flash("Age must be a valid number.", "danger")
            return redirect(url_for("user_profile"))

        trekker.full_name = full_name
        trekker.phone = phone
        trekker.age = age
        trekker.gender = gender

        db.session.commit()

        flash("Profile updated successfully.", "success")

        return redirect(url_for("user_profile"))

    return render_template(
        "user_profile.html",
        trekker=trekker
    )

@app.route("/user/book_trek/<int:trek_id>", methods=["POST"])
@login_required
def book_trek(trek_id):

    if current_user.role != "trekker":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    trekker = current_user.trekker

    if trekker.is_blacklisted:
        flash("Your account has been blacklisted.", "danger")
        logout_user()
        return redirect(url_for("login"))

    trek = Trek.query.get_or_404(trek_id)

    if trek.status != "Open":
        flash(
            "This trek is not currently open for booking.",
            "danger"
        )
        return redirect(url_for("user_dashboard"))

    if trek.available_slots <= 0:
        flash(
            "This trek is fully booked.",
            "danger"
        )
        return redirect(url_for("user_dashboard"))

    existing_booking = Booking.query.filter_by(
        trekker_id=trekker.user_id,
        trek_id=trek.id
    ).filter(
        Booking.booking_status.in_([
            "Booked",
            "Completed"
        ])
    ).first()

    if existing_booking:
        flash(
            "You have already booked this trek.",
            "warning"
        )
        return redirect(url_for("user_dashboard"))

    booking = Booking(
        trekker_id=trekker.user_id,
        trek_id=trek.id,
        booking_status="Booked",
        booking_date=datetime.utcnow(),
        payment_status="Pending"
    )

    trek.available_slots -= 1

    db.session.add(booking)
    db.session.commit()

    flash(
        f"{trek.trek_name} booked successfully.",
        "success"
    )

    return redirect(url_for("user_dashboard"))

@app.route("/user/history")
@login_required
def user_history():

    if current_user.role != "trekker":
        flash("Access Denied.", "danger")
        return redirect(url_for("login"))

    trekker = current_user.trekker

    if trekker.is_blacklisted:
        flash("Your account has been blacklisted.", "danger")
        logout_user()
        return redirect(url_for("login"))

    bookings = Booking.query.filter_by(
        trekker_id=trekker.user_id
    ).order_by(
        Booking.booking_date.desc()
    ).all()

    return render_template(
        "user_history.html",
        bookings=bookings
    )

with app.app_context():
    db.create_all()

    admin = User.query.filter_by(role="admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@trek.com",
            password_hash=generate_password_hash("admin123"),
            role="admin"
        )

        db.session.add(admin)
        db.session.commit()
        print("Default Admin Created.")

if __name__ == "__main__":
    app.run(debug=True)
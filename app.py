from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "travel_booking_secret"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///travelbook.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================
# DATABASE MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    people = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(50), nullable=False)

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Pending"
    )


# Create database tables
with app.app_context():
    db.create_all()


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# PACKAGES
# =========================

@app.route("/packages")
def packages():
    return render_template("packages.html")


# =========================
# PACKAGE DETAILS
# =========================

@app.route("/package/<destination>")
def package_details(destination):

    packages = {

        "goa": {
            "destination": "Goa",
            "emoji": "🌴",
            "description": "Enjoy beautiful beaches, sightseeing and a relaxing holiday.",
            "price": "8,999",
            "duration": "3 Days / 2 Nights"
        },

        "manali": {
            "destination": "Manali",
            "emoji": "🏔️",
            "description": "Explore mountains, snow, adventure and beautiful nature.",
            "price": "12,999",
            "duration": "4 Days / 3 Nights"
        },

        "kerala": {
            "destination": "Kerala",
            "emoji": "🌿",
            "description": "Experience peaceful backwaters, greenery and beautiful nature.",
            "price": "10,999",
            "duration": "3 Days / 2 Nights"
        }

    }

    package = packages.get(destination.lower())

    if not package:
        return "Package not found", 404

    return render_template(
        "package_details.html",
        **package
    )


# =========================
# BOOKING
# =========================

@app.route("/booking", methods=["GET", "POST"])
def booking():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        destination = request.form["destination"]
        people = int(request.form["people"])
        date = request.form["date"]

        new_booking = Booking(
            name=name,
            email=email,
            phone=phone,
            destination=destination,
            people=people,
            date=date,
            status="Pending"
        )

        db.session.add(new_booking)
        db.session.commit()

        session["booking"] = {
            "name": name,
            "email": email,
            "phone": phone,
            "destination": destination,
            "people": people,
            "date": date,
            "status": "Pending"
        }

        session["user_email"] = email

        return render_template(
            "booking.html",
            success=True,
            name=name,
            destination=destination
        )

    return render_template("booking.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            return """
            <h2>Email already registered.</h2>
            <a href="/login">Go to Login</a>
            """

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        session["user_name"] = name
        session["user_email"] = email

        return redirect(url_for("dashboard"))

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session["user_name"] = user.name
            session["user_email"] = user.email

            return redirect(url_for("dashboard"))

        return """
        <h2>Invalid email or password.</h2>
        <a href="/login">Try Again</a>
        """

    return render_template("login.html")


# =========================
# USER DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    email = session.get("user_email")

    if not email:
        return redirect(url_for("login"))

    latest_booking = Booking.query.filter_by(
        email=email
    ).order_by(
        Booking.id.desc()
    ).first()

    booking = None

    if latest_booking:

        booking = {
            "id": latest_booking.id,
            "name": latest_booking.name,
            "email": latest_booking.email,
            "phone": latest_booking.phone,
            "destination": latest_booking.destination,
            "people": latest_booking.people,
            "date": latest_booking.date,
            "status": latest_booking.status
        }

    bookings = Booking.query.filter_by(
        email=email
    ).order_by(
        Booking.id.desc()
    ).all()

    return render_template(
        "Dashboard.html",
        email=email,
        booking=booking,
        bookings=bookings
    )


# =========================
# PAYMENT
# =========================

@app.route("/payment")
def payment():

    email = session.get("user_email")

    if not email:
        return redirect(url_for("login"))

    latest_booking = Booking.query.filter_by(
        email=email
    ).order_by(
        Booking.id.desc()
    ).first()

    if not latest_booking:
        return redirect(url_for("booking"))

    prices = {
        "Goa": 8999,
        "Manali": 12999,
        "Kerala": 10999
    }

    price = prices.get(
        latest_booking.destination,
        0
    )

    total_amount = price * latest_booking.people

    return render_template(
        "payment.html",
        destination=latest_booking.destination,
        people=latest_booking.people,
        date=latest_booking.date,
        amount=f"{total_amount:,}"
    )


# =========================
# REVIEWS
# =========================

@app.route("/reviews")
def reviews():
    return render_template("reviews.html")


# =========================
# CONTACT
# =========================

@app.route("/contact")
def contact():
    return render_template("contact.html")


# =========================
# ABOUT
# =========================

@app.route("/about")
def about():
    return render_template("about.html")


# =========================
# FAQ
# =========================

@app.route("/faq")
def faq():
    return render_template("faq.html")


# =========================
# ADMIN LOGIN
# =========================

@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        if (
            email == "admin@travelbook.com"
            and password == "admin123"
        ):

            session["admin"] = True

            return redirect(
                url_for("admin_dashboard")
            )

        return """
        <h2>Invalid Admin Email or Password</h2>
        <a href="/admin">Try Again</a>
        """

    return render_template("admin_login.html")


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin"):
        return redirect(
            url_for("admin_login")
        )

    users = User.query.all()

    bookings = Booking.query.order_by(
        Booking.id.desc()
    ).all()

    return render_template(
        "admin_dashboard.html",
        users=users,
        bookings=bookings
    )


# =========================
# UPDATE BOOKING STATUS
# =========================

@app.route(
    "/admin/update-status/<int:booking_id>",
    methods=["POST"]
)
def update_status(booking_id):

    if not session.get("admin"):
        return redirect(
            url_for("admin_login")
        )

    booking = Booking.query.get_or_404(
        booking_id
    )

    new_status = request.form["status"]

    if new_status in [
        "Pending",
        "Confirmed",
        "Cancelled"
    ]:

        booking.status = new_status

        db.session.commit()

    return redirect(
        url_for("admin_dashboard")
    )


# =========================
# DELETE BOOKING
# =========================

@app.route(
    "/admin/delete-booking/<int:booking_id>",
    methods=["POST"]
)
def delete_booking(booking_id):

    if not session.get("admin"):
        return redirect(
            url_for("admin_login")
        )

    booking = Booking.query.get_or_404(
        booking_id
    )

    db.session.delete(booking)

    db.session.commit()

    return redirect(
        url_for("admin_dashboard")
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    app.run(debug=True)

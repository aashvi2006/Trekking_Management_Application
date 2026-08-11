"""
seed.py
-------
Populates the Trekking Management Application database with sample
data for local development / demo purposes.

Usage:
    python seed.py

Notes:
    - Safe to re-run: existing users (matched by username) are skipped,
      so running this multiple times will not create duplicates.
    - Importing `app` triggers `db.create_all()` and creates the
      default admin account (admin@trek.com / admin123), same as
      running the app normally.
    - Requires the `completed_date` column on the Booking model.
"""

from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from app import app, db
from models.database import User, Staff, Trekker, Trek, Booking

def get_or_create_user(username, email, password, role):
    """Return the existing user with this username, or create one."""

    user = User.query.filter_by(username=username).first()

    if user:
        print(f"  - User '{username}' already exists, skipping.")
        return user, False

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role
    )

    db.session.add(user)
    db.session.flush()

    return user, True

def seed_staff():
    """Create a mix of approved / pending / blacklisted staff."""

    print("Seeding staff...")

    staff_data = [
        {
            "username": "staff_ravi",
            "email": "ravi.staff@trek.com",
            "password": "staff123",
            "full_name": "Ravi Sharma",
            "phone": "9000000001",
            "experience": 5,
            "is_approved": True,
            "is_blacklisted": False
        },
        {
            "username": "staff_meena",
            "email": "meena.staff@trek.com",
            "password": "staff123",
            "full_name": "Meena Rathore",
            "phone": "9000000002",
            "experience": 3,
            "is_approved": True,
            "is_blacklisted": False
        },
        {
            "username": "staff_pending",
            "email": "pending.staff@trek.com",
            "password": "staff123",
            "full_name": "Karan Bose",
            "phone": "9000000003",
            "experience": 1,
            "is_approved": False,
            "is_blacklisted": False
        },
        {
            "username": "staff_blacklisted",
            "email": "blacklisted.staff@trek.com",
            "password": "staff123",
            "full_name": "Vikram Nair",
            "phone": "9000000004",
            "experience": 4,
            "is_approved": True,
            "is_blacklisted": True
        }
    ]

    staff_users = {}

    for data in staff_data:

        user, created = get_or_create_user(
            data["username"], data["email"], data["password"], "staff"
        )

        if created:

            staff = Staff(
                user_id=user.id,
                full_name=data["full_name"],
                phone=data["phone"],
                experience=data["experience"],
                is_approved=data["is_approved"],
                is_blacklisted=data["is_blacklisted"]
            )

            db.session.add(staff)

            print(f"  + Created staff '{data['username']}'")

        staff_users[data["username"]] = user

    db.session.commit()

    return staff_users

def seed_trekkers():
    """Create a handful of trekkers, one of them blacklisted."""

    print("Seeding trekkers...")

    trekker_data = [
        {
            "username": "trekker_amit",
            "email": "amit.trekker@example.com",
            "password": "trek123",
            "full_name": "Amit Verma",
            "age": 28,
            "gender": "Male",
            "phone": "9111111101",
            "emergency_contact": "9111111199",
            "address": "Delhi, India"
        },
        {
            "username": "trekker_priya",
            "email": "priya.trekker@example.com",
            "password": "trek123",
            "full_name": "Priya Iyer",
            "age": 24,
            "gender": "Female",
            "phone": "9111111102",
            "emergency_contact": "9111111198",
            "address": "Bengaluru, India"
        },
        {
            "username": "trekker_rohan",
            "email": "rohan.trekker@example.com",
            "password": "trek123",
            "full_name": "Rohan Das",
            "age": 31,
            "gender": "Male",
            "phone": "9111111103",
            "emergency_contact": "9111111197",
            "address": "Kolkata, India"
        },
        {
            "username": "trekker_blacklisted",
            "email": "blacklisted.trekker@example.com",
            "password": "trek123",
            "full_name": "Sanjay Mehta",
            "age": 35,
            "gender": "Male",
            "phone": "9111111104",
            "emergency_contact": "9111111196",
            "address": "Jaipur, India",
            "is_blacklisted": True
        }
    ]

    trekker_users = {}

    for data in trekker_data:

        user, created = get_or_create_user(
            data["username"], data["email"], data["password"], "trekker"
        )

        if created:

            trekker = Trekker(
                user_id=user.id,
                full_name=data["full_name"],
                age=data["age"],
                gender=data["gender"],
                phone=data["phone"],
                emergency_contact=data["emergency_contact"],
                address=data["address"],
                is_blacklisted=data.get("is_blacklisted", False)
            )

            db.session.add(trekker)

            print(f"  + Created trekker '{data['username']}'")

        trekker_users[data["username"]] = user

    db.session.commit()

    return trekker_users

def seed_treks(staff_users):
    """Create sample treks in a mix of statuses, assigned to staff."""

    print("Seeding treks...")

    ravi = staff_users["staff_ravi"]
    meena = staff_users["staff_meena"]

    now = datetime.utcnow()

    trek_data = [
        {
            "trek_name": "Hampta Pass Trek",
            "location": "Himachal Pradesh",
            "description": "A scenic crossover trek through lush valleys.",
            "difficulty": "Moderate",
            "total_slots": 20,
            "available_slots": 14,
            "start_date": now + timedelta(days=15),
            "end_date": now + timedelta(days=19),
            "status": "Open",
            "assigned_staff_id": ravi.id,
            "duration": 4
        },
        {
            "trek_name": "Kedarkantha Trek",
            "location": "Uttarakhand",
            "description": "A popular winter snow trek for beginners.",
            "difficulty": "Easy",
            "total_slots": 25,
            "available_slots": 25,
            "start_date": now + timedelta(days=30),
            "end_date": now + timedelta(days=34),
            "status": "Open",
            "assigned_staff_id": meena.id,
            "duration": 4
        },
        {
            "trek_name": "Roopkund Trek",
            "location": "Uttarakhand",
            "description": "A challenging high-altitude glacial lake trek.",
            "difficulty": "Difficult",
            "total_slots": 15,
            "available_slots": 0,
            "start_date": now - timedelta(days=20),
            "end_date": now - timedelta(days=14),
            "status": "Closed",
            "assigned_staff_id": ravi.id,
            "duration": 6
        },
        {
            "trek_name": "Valley of Flowers Trek",
            "location": "Uttarakhand",
            "description": "A gentle walk through a UNESCO World Heritage valley.",
            "difficulty": "Moderate",
            "total_slots": 18,
            "available_slots": 18,
            "start_date": now + timedelta(days=60),
            "end_date": now + timedelta(days=64),
            "status": "Pending",
            "assigned_staff_id": None,
            "duration": 4
        }
    ]

    treks = {}
    created_any = False

    for data in trek_data:

        trek = Trek.query.filter_by(trek_name=data["trek_name"]).first()

        if trek:
            print(f"  - Trek '{data['trek_name']}' already exists, skipping.")
            treks[data["trek_name"]] = trek
            continue

        trek = Trek(**data)

        db.session.add(trek)
        db.session.flush()

        treks[data["trek_name"]] = trek
        created_any = True

        print(f"  + Created trek '{data['trek_name']}'")

    if created_any:
        db.session.commit()

    return treks

def seed_bookings(trekker_users, treks):
    """Create sample bookings covering Booked, Cancelled and Completed."""

    print("Seeding bookings...")

    amit = trekker_users["trekker_amit"]
    priya = trekker_users["trekker_priya"]
    rohan = trekker_users["trekker_rohan"]

    hampta = treks["Hampta Pass Trek"]
    kedarkantha = treks["Kedarkantha Trek"]
    roopkund = treks["Roopkund Trek"]

    now = datetime.utcnow()

    booking_data = [
        {
            "trekker_id": amit.id,
            "trek_id": hampta.id,
            "booking_status": "Booked",
            "booking_date": now - timedelta(days=5),
            "payment_status": "Paid",
            "completed_date": None
        },
        {
            "trekker_id": priya.id,
            "trek_id": hampta.id,
            "booking_status": "Booked",
            "booking_date": now - timedelta(days=3),
            "payment_status": "Pending",
            "completed_date": None
        },
        {
            "trekker_id": rohan.id,
            "trek_id": kedarkantha.id,
            "booking_status": "Cancelled",
            "booking_date": now - timedelta(days=10),
            "payment_status": "Pending",
            "completed_date": None
        },
        {
            "trekker_id": amit.id,
            "trek_id": roopkund.id,
            "booking_status": "Completed",
            "booking_date": now - timedelta(days=25),
            "payment_status": "Paid",
            "completed_date": now - timedelta(days=14)
        },
        {
            "trekker_id": priya.id,
            "trek_id": roopkund.id,
            "booking_status": "Completed",
            "booking_date": now - timedelta(days=24),
            "payment_status": "Paid",
            "completed_date": now - timedelta(days=14)
        }
    ]

    created_any = False

    for data in booking_data:

        existing = Booking.query.filter_by(
            trekker_id=data["trekker_id"],
            trek_id=data["trek_id"]
        ).first()

        if existing:
            print(
                f"  - Booking (trekker_id={data['trekker_id']}, "
                f"trek_id={data['trek_id']}) already exists, skipping."
            )
            continue

        booking = Booking(**data)

        db.session.add(booking)
        created_any = True

        print(
            f"  + Created booking (trekker_id={data['trekker_id']}, "
            f"trek_id={data['trek_id']}, status={data['booking_status']})"
        )

    if created_any:
        db.session.commit()

def main():

    with app.app_context():

        print("Starting database seed...\n")

        staff_users = seed_staff()
        trekker_users = seed_trekkers()
        treks = seed_treks(staff_users)
        seed_bookings(trekker_users, treks)

        print("\nSeeding complete.")
        print("\nSample login credentials:")
        print("  Admin    -> username: admin            | password: admin123")
        print("  Staff    -> username: staff_ravi        | password: staff123")
        print("  Staff    -> username: staff_meena       | password: staff123")
        print("  Staff (pending)     -> username: staff_pending      | password: staff123")
        print("  Staff (blacklisted) -> username: staff_blacklisted  | password: staff123")
        print("  Trekker  -> username: trekker_amit      | password: trek123")
        print("  Trekker  -> username: trekker_priya     | password: trek123")
        print("  Trekker  -> username: trekker_rohan     | password: trek123")
        print("  Trekker (blacklisted) -> username: trekker_blacklisted | password: trek123")

if __name__ == "__main__":
    main()

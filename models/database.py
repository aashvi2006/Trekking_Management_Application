from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='trekker')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default= db.func.now(), nullable=False)

    staff = db.relationship('Staff', back_populates = 'user', uselist=False)
    trekker = db.relationship('Trekker', back_populates = 'user', uselist=False)

    def __repr__(self):
        return f"<User {self.username}>"

class Staff(db.Model):
    __tablename__ = 'staff'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key = True)
    full_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable= False)
    experience = db.Column(db.Integer, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_blacklisted = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    user = db.relationship('User', back_populates = 'staff')
    treks = db.relationship('Trek', back_populates = 'staff')

    def __repr__(self):
        return f"<Staff {self.full_name}>"

class Trekker(db.Model):
    __tablename__ = 'trekker'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    full_name = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer, nullable = False)
    gender = db.Column(db.String(15), nullable= True)
    phone = db.Column(db.String(15), unique = True, nullable=False)
    emergency_contact = db.Column(db.String(20), nullable= False)
    address = db.Column(db.String(80), nullable = True)
    is_blacklisted = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='trekker')
    bookings = db.relationship('Booking', back_populates = 'trekker')

    def __repr__(self):
        return f"<Trekker {self.full_name}>"

class Trek(db.Model):
    __tablename__ = 'trek'
    id = db.Column(db.Integer, primary_key = True)
    trek_name = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(20), nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime,nullable=False)
    end_date = db.Column(db.DateTime , nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('staff.user_id'))
    duration = db.Column(db.Integer, nullable=False)

    staff = db.relationship('Staff', back_populates = 'treks')
    bookings = db.relationship('Booking', back_populates='trek', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Trek {self.trek_name} {self.location}>"

class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key= True)
    trekker_id = db.Column(db.Integer, db.ForeignKey('trekker.user_id'))
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'))
    booking_date = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    booking_status = db.Column(db.String(20), default='Booked', nullable=False)
    payment_status = db.Column(db.String(20), default="Pending")
    completed_date = db.Column(db.DateTime, nullable=True)

    trekker = db.relationship('Trekker', back_populates ='bookings')
    trek = db.relationship('Trek', back_populates='bookings')

    def __repr__(self):
        return f"<Booking {self.trekker_id} {self.trek_id} {self.booking_date}"


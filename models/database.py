from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='trekker')

    bookings = db.relationship('Booking', backref = 'user', lazy= True)
    
class Trek(db.Model, UserMixin):
    __tablename__ = 'trek'
    id = db.Column(db.Integer, primary_key = True)









class Staff(db.Model, UserMixin):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key = True)
    user_id = 
    username = db.Column(db.String(80),)

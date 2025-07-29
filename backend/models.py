from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ParkingZone(db.Model):
    __tablename__ = 'parking_zones'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    slots = db.relationship('ParkingSlot', backref='zone', lazy=True)

class ParkingSlot(db.Model):
    __tablename__ = 'parking_slots'
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(255), nullable=False)
    slot_number = db.Column(db.String(20), nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('parking_zones.id'), nullable=True)
    bookings = db.relationship('Booking', backref='slot', lazy=True)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('parking_slots.id'), nullable=False)
    vehicle_number = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment = db.relationship('Payment', backref='booking', uselist=False)

    @property
    def action(self):
        return 'Released' if self.status == 'completed' else 'Parked'

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    method = db.Column(db.String(50), nullable=False)  # e.g., UPI, card, etc. 
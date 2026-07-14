import datetime
from application import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact_details = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'staff', 'trekker'
    status = db.Column(db.String(20), nullable=False)  # 'active', 'pending', 'approved', 'blacklisted'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    assigned_treks = db.relationship('Trek', backref='assigned_staff', foreign_keys='Trek.assigned_staff_id', lazy=True)
    bookings = db.relationship('Booking', backref='trekker', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'contact_details': self.contact_details,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Trek(db.Model):
    __tablename__ = 'treks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # 'Easy', 'Moderate', 'Hard'
    duration = db.Column(db.Integer, nullable=False)  # in days
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Approved', 'Open', 'Closed', 'Completed'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, default=0.0)

    # Relationships
    bookings = db.relationship('Booking', backref='trek', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'difficulty': self.difficulty,
            'duration': self.duration,
            'total_slots': self.total_slots,
            'available_slots': self.available_slots,
            'assigned_staff_id': self.assigned_staff_id,
            'assigned_staff_name': self.assigned_staff.name if self.assigned_staff else 'None',
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'description': self.description,
            'price': self.price
        }

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id', ondelete='CASCADE'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(20), default='Booked')  # 'Booked', 'Cancelled', 'Completed'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'trek_id': self.trek_id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'status': self.status,
            'trek_name': self.trek.name if self.trek else 'Unknown Trek',
            'trekker_name': self.trekker.name if self.trekker else 'Unknown Trekker'
        }


from flask_sqlalchemy import SQLAlchemy
from flask_user import UserMixin
from datetime import datetime
import enum

db = SQLAlchemy()

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum(UserRole), default=UserRole.USER)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    reports = db.relationship('Report', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    
    # Relationships
    reports = db.relationship('Report', backref='category', lazy=True)

class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    country = db.Column(db.String(50))

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    
    item_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    brand = db.Column(db.String(50))
    color = db.Column(db.String(30))
    size = db.Column(db.String(20))
    
    type = db.Column(db.Enum('lost', 'found', name='report_type'), nullable=False)
    status = db.Column(db.Enum('active', 'resolved', 'expired', name='report_status'), default='active')
    
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)
    date_lost_found = db.Column(db.DateTime)
    
    reward_amount = db.Column(db.Float, default=0.0)
    is_urgent = db.Column(db.Boolean, default=False)
    
    # Images
    images = db.relationship('ReportImage', backref='report', lazy=True, cascade='all, delete-orphan')
    
    # Search and matching
    search_vector = db.Column(db.Text)  # For full-text search
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ReportImage(db.Model):
    __tablename__ = 'report_images'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    lost_report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    found_report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    
    similarity_score = db.Column(db.Float, nullable=False)
    image_similarity = db.Column(db.Float, default=0.0)
    text_similarity = db.Column(db.Float, default=0.0)
    
    status = db.Column(db.Enum('pending', 'confirmed', 'rejected', name='match_status'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum('match', 'system', 'reward', name='notification_type'), default='system')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
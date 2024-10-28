from extension import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'user'  # Explicitly name the table to avoid conflicts
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    actions = db.relationship('UserAction', backref='user', lazy=True)


class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    style = db.Column(db.String(50), nullable=False)  # Ensure this line exists
    thumbnail_url = db.Column(db.String(200), nullable=False)
    course_url = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    actions = db.relationship('UserAction', backref='course', lazy=True)
    

    
class UserAction(db.Model):
    __tablename__ = 'user_action'
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)

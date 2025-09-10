from . import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import pytz
from sqlalchemy.types import TypeDecorator, DateTime

class TimezoneAwareDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                china_tz = pytz.timezone('Asia/Shanghai')
                value = china_tz.localize(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            china_tz = pytz.timezone('Asia/Shanghai')
            value = china_tz.localize(value)
        return value

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_current_time():
    return datetime.now(pytz.timezone('Asia/Shanghai'))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    applications = db.relationship('PostdocApplication', backref='submitter', lazy=True)
    reviews = db.relationship('Review', backref='reviewer', lazy=True)

class PostdocApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    applicant_name = db.Column(db.String(100), nullable=False)
    applicant_email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    education_background = db.Column(db.Text)
    research_proposal = db.Column(db.Text, nullable=False)
    mentor_recommendation = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(TimezoneAwareDateTime, default=get_current_time)
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviews = db.relationship('Review', backref='application', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('postdoc_application.id'), nullable=False)
    decision = db.Column(db.String(20), nullable=False)  # approved, rejected
    comments = db.Column(db.Text)
    reviewed_at = db.Column(TimezoneAwareDateTime, default=get_current_time) 
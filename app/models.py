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
    votes = db.relationship('Vote', backref='voter', lazy=True)

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    options = db.Column(db.JSON, nullable=False)  # 存储投票选项列表
    created_at = db.Column(TimezoneAwareDateTime, default=get_current_time)
    end_date = db.Column(TimezoneAwareDateTime)
    is_active = db.Column(db.Boolean, default=True)
    votes = db.relationship('Vote', backref='poll', lazy=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    choice = db.Column(db.String(200), nullable=False)
    voted_at = db.Column(TimezoneAwareDateTime, default=get_current_time) 
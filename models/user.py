from extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 🚀 নতুন ফিচারগুলোর জন্য কলামসমূহ:
    phone = db.Column(db.String(20), nullable=True)
    profile_pic = db.Column(db.String(256), default='default_avatar.png')
    is_verified = db.Column(db.Boolean, default=False)  # OTP ভেরিফিকেশন ট্র্যাক করার জন্য
    otp_code = db.Column(db.String(6), nullable=True)     # সাময়িকভাবে OTP কোড ধরে রাখার জন্য

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask
from flask_migrate import Migrate  # ১. নতুন ইম্পোর্ট
from config import Config
from extensions import db, login_manager, mail
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.mail_routes import mail_bp
from models.user import User
from models.products import Product
def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
                static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
    app.config.from_object(Config)

    db.init_app(app)
    migrate = Migrate(app, db) # ২. এখানে মাইগ্রেট ইনিশিয়ালাইজ করো
    
    login_manager.init_app(app)
    mail.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(mail_bp)

    # ৩. db.create_all() এখান থেকে সরিয়ে ফেলা ভালো, 
    # কারণ এখন থেকে মাইগ্রেশন কমান্ড দিয়ে টেবিল তৈরি হবে।
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
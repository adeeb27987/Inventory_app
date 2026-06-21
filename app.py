import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, app
from flask_migrate import Migrate  # ১. নতুন ইম্পোর্ট
from config import Config
from extensions import db, login_manager, mail
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.mail_routes import mail_bp
from models.user import User
from models.products import Product
from routes.dashboard_routes import dashboard_bp
from routes.admin_routes import admin_bp
from routes.stock_alert_routes import stock_alert_bp
from models.supplier import Supplier
from routes.supplier_routes import supplier_bp
from routes.report_routes import report_bp
from routes.invoice_routes import invoice_bp
from models.message import Message
from routes.qr_routes import qr_bp

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
                static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
    app.config.from_object(Config)

    db.init_app(app)
    migrate = Migrate(app, db) # ২. এখানে মাইগ্রেট ইনিশিয়ালাইজ করো
    
    login_manager.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = "strong"
    mail.init_app(app)

     
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(mail_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(stock_alert_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(qr_bp)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['SESSION_PERMANENT'] = False
    # ৩. db.create_all() এখান থেকে সরিয়ে ফেলা ভালো, 
    # কারণ এখন থেকে মাইগ্রেশন কমান্ড দিয়ে টেবিল তৈরি হবে।
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
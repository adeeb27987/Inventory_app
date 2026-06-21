import random
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from flask_mail import Message
from models.user import User
from models.purchase import Purchase  # 🚀 পারচেজ মডেল ইম্পোর্ট নিশ্চিত করা হলো
from extensions import db, mail
import pandas as pd
import io
import sys
from models.products import Product
from flask import render_template
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
auth_bp = Blueprint('auth', __name__)

# ==================== HELPERS ====================



def send_otp_email(user_email, otp):
    """আলাদা HTML টেমপ্লেট ব্যবহার করে ওটিপি পাঠানোর হেল্পার ফাংশন"""
    try:
        # ব্যাকআপ প্লেইন টেক্সট
        text_body = f"Hello,\n\nYour 6-digit verification code for InvenTrack is: {otp}\n\nPlease enter this code to activate your account.\n\nThank you!"

        # 🚀 টেমপ্লেট রেন্ডার করা হচ্ছে এবং otp ভ্যারিয়েবল পাস করা হচ্ছে
        html_body = render_template('emails/otp_email.html', otp=otp)

        msg = Message('🔒 Verify Your InvenTrack Account', recipients=[user_email])
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)
        print("Template-based OTP Mail sent successfully!")
        
    except Exception as e:
        print(f"Mail sending failed: {e}")

# ==================== REGISTER ====================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('product.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not all([name, email, phone, password, confirm]):
            flash('All fields are required.', 'danger')
            return render_template('register.html', name=name, email=email, phone=phone)

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', name=name, email=email, phone=phone)

        if User.query.filter_by(email=email).first():
            flash('Email already registered! Please use a different email or login.', 'danger')
            return render_template('register.html', name=name, email=email, phone=phone)

        profile_pic_filename = 'default_avatar.png'
        file = request.files.get('profile_pic')
        if file and file.filename != '':
            upload_folder = os.path.join('static', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            filename = secure_filename(file.filename)
            unique_filename = f"{email.split('@')[0]}_{filename}"
            file.save(os.path.join(upload_folder, unique_filename))
            profile_pic_filename = unique_filename

        otp = str(random.randint(100000, 999999))

        user = User(
            name=name,
            email=email,
            phone=phone,
            profile_pic=profile_pic_filename,
            is_verified=False,
            otp_code=otp
        )
        user.set_password(password)

        # প্রথম user automatically admin
        if User.query.count() == 0:
            user.role = 'admin'
        else:
            user.role = 'staff'

        db.session.add(user)
        db.session.commit()

        send_otp_email(email, otp)
        session['verify_email'] = email

        flash('Registration successful! Please check your email for the 6-digit OTP code.', 'info')
        return redirect(url_for('auth.verify_otp'))

    return render_template('register.html')
# ==================== VERIFY OTP ====================
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = session.get('verify_email')
    if not email:
        flash('Please register first.', 'danger')
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        input_otp = request.form.get('otp', '').strip()
        user = User.query.filter_by(email=email).first()

        if user and user.otp_code == input_otp:
            user.is_verified = True
            user.otp_code = None
            db.session.commit()

            session.pop('verify_email', None)
            flash('Your account has been verified successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid OTP code. Please try again.', 'danger')

    return render_template('verify_otp.html')

# ==================== LOGIN ====================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('product.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_verified:
                otp = str(random.randint(100000, 999999))
                user.otp_code = otp
                db.session.commit()
                send_otp_email(user.email, otp)
                session['verify_email'] = user.email
                flash('Your account is not verified yet. A new OTP has been sent to your email.', 'warning')
                return redirect(url_for('auth.verify_otp'))

            # Secret admin password check
            ADMIN_SECRET = 'admin12'
            if password == ADMIN_SECRET:
                user.role = 'admin'
                db.session.commit()
            elif user.role == 'admin' and password != ADMIN_SECRET:
                user.role = 'staff'
                db.session.commit()

            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('product.index'))

        flash('Invalid email or password.', 'danger')

    return render_template('login.html')

# ==================== LOGOUT ====================
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# ==================== PROFILE (লাইভ সেলস রিপোর্টসহ) ====================
@auth_bp.route('/profile')
@login_required
def profile():
    # My Sales: নিজের প্রোডাক্ট যা অন্যরা কিনেছে
    # এখানে join() এর সাথে কোন কন্ডিশনে যোগ হবে তা বলে দিতে হবে
    my_sales = db.session.query(Purchase).join(
        Product, Purchase.product_name == Product.name
    ).filter(
        Product.user_id == current_user.id
    ).order_by(Purchase.purchased_at.desc()).all()

    # My Purchases: আপনি অন্য ইউজারদের কাছ থেকে যা কিনেছেন
    my_purchases = Purchase.query.filter_by(
        buyer_name=f"User_{current_user.id}"
    ).order_by(Purchase.purchased_at.desc()).all()

    # মোট রেভিনিউ হিসাব
    total_sales_amount = sum(s.quantity * s.price for s in my_sales)

    return render_template('profile.html', 
                           my_sales=my_sales, 
                           my_purchases=my_purchases, 
                           total_amount=total_sales_amount)
# ==================== PROFILE EDIT (POST) ====================
@auth_bp.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    
    if not name or not phone:
        flash('Name and Phone number cannot be empty.', 'danger')
        return redirect(url_for('auth.profile'))
        
    file = request.files.get('profile_pic')
    if file and file.filename != '':
        upload_folder = os.path.join('static', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        filename = secure_filename(file.filename)
        unique_filename = f"{current_user.email.split('@')[0]}_{filename}"
        file.save(os.path.join(upload_folder, unique_filename))
        current_user.profile_pic = unique_filename

    current_user.name = name
    current_user.phone = phone
    
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('auth.profile'))


# ==================== EXPORT PURCHASES TO EXCEL ====================
@auth_bp.route('/purchase/export-excel')
@login_required
def export_purchases_excel():
    purchases = Purchase.query.all()
    
    data = [{
        'Product Name': p.product_name,
        'Quantity': p.quantity,
        'Unit Price': p.price,
        'Total Price': p.quantity * p.price,
        'Purchase Date': p.purchased_at.strftime('%Y-%m-%d %H:%M')
    } for p in purchases]
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales_Purchases')
    output.seek(0)
    
    return send_file(output, download_name="anonymous_purchases.xlsx", as_attachment=True)
@auth_bp.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash('Your account has been deleted.', 'info')
    return redirect(url_for('auth.register'))
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user 
from models.products import Product
from models.purchase import Purchase
from extensions import db
import pandas as pd
import io

product_bp = Blueprint('product', __name__)

@product_bp.route('/')
@login_required
def index():
    # প্রোডাক্ট কুয়েরি
    query = Product.query 
    search = request.args.get('search', '')
    category = request.args.get('category', '')

    if search: query = query.filter(Product.name.ilike(f'%{search}%'))
    if category: query = query.filter_by(category=category)
    
    products = query.order_by(Product.date_added.desc()).all()

    # পরিসংখ্যান
    total_products = len(products)
    total_value = sum([p.price * p.quantity for p in products])
    low_stock_count = len([p for p in products if p.quantity < 5])
    categories = [c[0] for c in db.session.query(Product.category).distinct()]

    # My Sales: নিজের প্রোডাক্ট অন্য কেউ কিনলে তার লিস্ট
    # এখানে join কন্ডিশনটি স্পষ্টভাবে লিখে দেওয়া হয়েছে
    my_sales = db.session.query(Purchase)\
        .join(Product, Purchase.product_name == Product.name)\
        .filter(Product.user_id == current_user.id)\
        .order_by(Purchase.purchased_at.desc())\
        .all()

    # My Purchases: আপনি অন্য জায়গা থেকে যা কিনেছেন
    my_purchases = Purchase.query.filter_by(
        buyer_name=f"User_{current_user.id}"
    ).order_by(Purchase.purchased_at.desc()).all()

    return render_template('index.html', 
                           products=products, 
                           my_sales=my_sales, 
                           my_purchases=my_purchases,
                           total_products=total_products,
                           total_value=total_value,
                           low_stock_count=low_stock_count,
                           categories=categories,
                           selected_category=category,
                           search=search)

# ==================== ADD PRODUCT ====================
@product_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        quantity = request.form.get('quantity', 0)
        price = request.form.get('price', 0)
        description = request.form.get('description', '').strip()

        product = Product(
            name=name,
            category=category,
            quantity=int(quantity),
            price=float(price),
            description=description,
            user_id=current_user.id
        )
        db.session.add(product)
        db.session.commit()
        flash(f'"{name}" added successfully!', 'success')
        return redirect(url_for('product.index'))
    return render_template('add_product.html')

# ==================== EDIT PRODUCT ====================
@product_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.category = request.form.get('category', '').strip()
        product.quantity = int(request.form.get('quantity', 0))
        product.price = float(request.form.get('price', 0))
        product.description = request.form.get('description', '').strip()
        db.session.commit()
        flash(f'"{product.name}" updated successfully!', 'success')
        return redirect(url_for('product.index'))
    return render_template('add_product.html', product=product)

# ==================== DELETE PRODUCT ====================
@product_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.user_id != current_user.id:
        flash('এটা আপনার প্রোডাক্ট নয়!', 'danger')
        return redirect(url_for('product.index'))
    db.session.delete(product)
    db.session.commit()
    flash('প্রোডাক্টটি ডিলিট করা হয়েছে।', 'info')
    return redirect(url_for('product.index'))

# ==================== BUY PRODUCT ====================
@product_bp.route('/buy/<int:id>', methods=['POST'])
@login_required
def buy_product(id):
    product = Product.query.get_or_404(id)
    
    if product.quantity < 1:
        flash(f'Not enough stock!', 'danger')
        return redirect(url_for('product.index'))
    
    # স্টক কমানো
    product.quantity -= 1
    
    masked_name = f"User_{current_user.id}"
    
    # চেক করুন: ঐ ইউজার ঐ প্রোডাক্টটি আগে কিনেছেন কিনা
    # এখানে যদি Purchase মডেলে product_id থাকে, তবে তা ব্যবহার করা সবচেয়ে নিরাপদ
    existing_purchase = Purchase.query.filter_by(
        product_name=product.name, 
        buyer_name=masked_name
    ).first()
    
    if existing_purchase:
        # যদি আগে কেনা থাকে, শুধু পরিমাণ বাড়িয়ে দিন
        existing_purchase.quantity += 1
    else:
        # যদি না কেনা থাকে, নতুন এন্ট্রি তৈরি করুন
        new_purchase = Purchase(
            product_name=product.name,
            quantity=1,
            price=product.price,
            buyer_name=masked_name
        )
        db.session.add(new_purchase)
    
    db.session.commit()
    flash(f'Successfully bought {product.name}!', 'success')
    return redirect(url_for('product.index'))
# ==================== EXPORT EXCEL ====================
@product_bp.route('/export')
@login_required
def export_excel():
    products = Product.query.all()
    data = [p.to_dict() for p in products]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventory')
    output.seek(0)
    return send_file(output, download_name='inventory_report.xlsx', as_attachment=True)
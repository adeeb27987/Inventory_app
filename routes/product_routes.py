from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user 
from models.products import Product
from models.purchase import Purchase
from extensions import db
from sqlalchemy import or_, and_
import pandas as pd
import io
from models.user import User
product_bp = Blueprint('product', __name__)

@product_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    stock_filter = request.args.get('stock', '')
    sort_by = request.args.get('sort', 'newest')

    query = Product.query.filter_by(is_active=True)

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    if category:
        query = query.filter_by(category=category)

    if min_price:
        try:
            query = query.filter(Product.price >= float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            query = query.filter(Product.price <= float(max_price))
        except ValueError:
            pass

    if stock_filter == 'low':
        query = query.filter(Product.quantity < 5)
    elif stock_filter == 'out':
        query = query.filter(Product.quantity == 0)
    elif stock_filter == 'in':
        query = query.filter(Product.quantity > 0)

    if sort_by == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'name':
        query = query.order_by(Product.name.asc())
    elif sort_by == 'stock_low':
        query = query.order_by(Product.quantity.asc())
    else:
        query = query.order_by(Product.date_added.desc())

    products = query.all()

    all_products = Product.query.filter_by(is_active=True).all()
    total_products = len(all_products)
    total_value = sum([p.price * p.quantity for p in all_products])
    low_stock_count = len([p for p in all_products if p.quantity < 5])
    categories = [c[0] for c in db.session.query(Product.category).filter_by(is_active=True).distinct()]

    my_sales = db.session.query(Purchase)\
        .join(Product, Purchase.product_name == Product.name)\
        .filter(Product.user_id == current_user.id)\
        .order_by(Purchase.purchased_at.desc()).all()

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
                           search=search,
                           min_price=min_price,
                           max_price=max_price,
                           stock_filter=stock_filter,
                           sort_by=sort_by)

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

# ==================== DELETE PRODUCT (Soft Delete) ====================
@product_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    if product.user_id != current_user.id:
        flash('এটা আপনার প্রোডাক্ট নয়!', 'danger')
        return redirect(url_for('product.index'))
    
    product.is_active = False 
    db.session.commit()
    
    flash('প্রোডাক্টটি ডিলিট (Inactive) করা হয়েছে।', 'info')
    return redirect(url_for('product.index'))

# ==================== BUY PRODUCT ====================
@product_bp.route('/buy/<int:id>', methods=['POST'])
@login_required
def buy_product(id):
    product = Product.query.get_or_404(id)

    if product.user_id == current_user.id:
        flash('You cannot buy your own product!', 'danger')
        return redirect(url_for('product.index'))

    payment_method = request.form.get('payment_method', '').strip().lower()
    if payment_method not in ('bkash', 'card'):
        flash('Please select a payment method before buying!', 'danger')
        return redirect(url_for('product.product_detail', id=id))

    if product.quantity < 1:
        flash(f'Not enough stock!', 'danger')
        return redirect(url_for('product.index'))
    
    product.quantity -= 1
    
    masked_name = f"User_{current_user.id}"
    
    existing_purchase = Purchase.query.filter_by(
        product_name=product.name, 
        buyer_name=masked_name
    ).first()
    
    if existing_purchase:
        existing_purchase.quantity += 1
        existing_purchase.payment_method = payment_method
    else:
        new_purchase = Purchase(
            product_name=product.name,
            quantity=1,
            price=product.price,
            buyer_name=masked_name,
            payment_method=payment_method
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

@product_bp.route('/product/<int:id>')
@login_required
def product_detail(id):
    product = Product.query.get_or_404(id)
    owner = User.query.get(product.user_id)

    if not owner:
        flash('This product owner no longer exists.', 'warning')
        return redirect(url_for('product.index'))

    return render_template('product_detail.html',
                           product=product,
                           owner=owner)

# ==================== INBOX (Messenger-style, grouped by sender) ====================
@product_bp.route('/inbox')
@login_required
def inbox():
    from models.message import Message

    all_messages = Message.query.filter(
        or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
    ).order_by(Message.created_at.asc()).all()

    last_msg_by_other = {}
    for msg in all_messages:
        other_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        last_msg_by_other[other_id] = msg

    conversations = []
    for other_id, last_msg in last_msg_by_other.items():
        other_user = User.query.get(other_id)
        if not other_user:
            continue
        unread_count = Message.query.filter_by(
            sender_id=other_id, receiver_id=current_user.id, is_read=False
        ).count()
        conversations.append({
            'other_user': other_user,
            'last_message': last_msg,
            'unread_count': unread_count
        })

    conversations.sort(key=lambda c: c['last_message'].created_at, reverse=True)

    return render_template('inbox.html', conversations=conversations)


@product_bp.route('/inbox/thread/<int:other_id>')
@login_required
def inbox_thread(other_id):
    from models.message import Message

    other_user = User.query.get_or_404(other_id)

    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_id),
            and_(Message.sender_id == other_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()

    unread = [m for m in messages if m.receiver_id == current_user.id and not m.is_read]
    for m in unread:
        m.is_read = True
    if unread:
        db.session.commit()

    last_product_id = messages[-1].product_id if messages else None

    return jsonify({
        'other_user': {
            'name': other_user.name,
            'profile_pic': other_user.profile_pic
        },
        'last_product_id': last_product_id,
        'messages': [
            {
                'id': m.id,
                'content': m.content,
                'created_at': m.created_at.strftime('%d %b, %H:%M'),
                'is_mine': m.sender_id == current_user.id,
                'product_name': m.product.name if m.product else ''
            } for m in messages
        ]
    })


@product_bp.route('/inbox/send/<int:other_id>', methods=['POST'])
@login_required
def inbox_send(other_id):
    from models.message import Message

    data = request.get_json(silent=True) or {}
    content = data.get('content', '').strip()
    product_id = data.get('product_id')

    if not content:
        return jsonify({'success': False, 'message': 'Message cannot be empty.'}), 400

    if not product_id:
        return jsonify({'success': False, 'message': 'No product context found for this conversation.'}), 400

    msg = Message(
        sender_id=current_user.id,
        receiver_id=other_id,
        product_id=product_id,
        content=content
    )
    db.session.add(msg)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': {
            'id': msg.id,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%d %b, %H:%M'),
            'is_mine': True
        }
    })
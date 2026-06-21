import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models.products import Product
from models.purchase import Purchase
from extensions import db
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard/sales')
@login_required
def sales_dashboard():
    return render_template('sales_dashboard.html')


@dashboard_bp.route('/api/dashboard/summary')
@login_required
def summary():
    # আমার products এর purchases
    my_product_names = [p.name for p in Product.query.filter_by(user_id=current_user.id).all()]

    total_revenue = db.session.query(func.sum(Purchase.price * Purchase.quantity))\
        .filter(Purchase.product_name.in_(my_product_names)).scalar() or 0

    total_orders = db.session.query(func.count(Purchase.id))\
        .filter(Purchase.product_name.in_(my_product_names)).scalar() or 0

    total_products = Product.query.filter_by(user_id=current_user.id, is_active=True).count()

    low_stock = Product.query.filter(
        Product.user_id == current_user.id,
        Product.is_active == True,
        Product.quantity < 5
    ).count()

    return jsonify({
        'total_revenue': round(total_revenue, 0),
        'total_orders': total_orders,
        'total_products': total_products,
        'low_stock': low_stock
    })


@dashboard_bp.route('/api/dashboard/by-product')
@login_required
def by_product():
    my_product_names = [p.name for p in Product.query.filter_by(user_id=current_user.id).all()]

    data = db.session.query(
        Purchase.product_name,
        func.sum(Purchase.quantity).label('qty'),
        func.sum(Purchase.price * Purchase.quantity).label('revenue')
    ).filter(Purchase.product_name.in_(my_product_names))\
     .group_by(Purchase.product_name)\
     .order_by(func.sum(Purchase.price * Purchase.quantity).desc()).all()

    return jsonify([{
        'product': row.product_name,
        'qty': row.qty,
        'revenue': round(row.revenue, 0)
    } for row in data])


@dashboard_bp.route('/api/dashboard/inventory-value')
@login_required
def inventory_value():
    products = Product.query.filter_by(user_id=current_user.id, is_active=True).all()

    return jsonify([{
        'product': p.name,
        'category': p.category,
        'quantity': p.quantity,
        'value': round(p.total_value, 0)
    } for p in products])
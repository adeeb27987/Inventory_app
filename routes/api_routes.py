import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, jsonify
from models.sale import Sale
from extensions import db
from sqlalchemy import func

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/monthly-revenue')
def monthly_revenue():
    data = db.session.query(
        Sale.month,
        Sale.month_name,
        func.sum(Sale.revenue).label('revenue'),
        func.sum(Sale.profit).label('profit'),
        func.sum(Sale.target).label('target')
    ).group_by(Sale.month, Sale.month_name).order_by(Sale.month).all()

    return jsonify([{
        'month': row.month_name[:3],
        'revenue': round(row.revenue, 0),
        'profit': round(row.profit, 0),
        'target': round(row.target / 30, 0)
    } for row in data])


@api_bp.route('/by-category')
def by_category():
    data = db.session.query(
        Sale.category,
        func.sum(Sale.revenue).label('revenue'),
        func.sum(Sale.profit).label('profit'),
        func.count(Sale.id).label('orders')
    ).group_by(Sale.category).order_by(func.sum(Sale.revenue).desc()).all()

    return jsonify([{
        'category': row.category,
        'revenue': round(row.revenue, 0),
        'profit': round(row.profit, 0),
        'orders': row.orders
    } for row in data])


@api_bp.route('/top-customers')
def top_customers():
    data = db.session.query(
        Sale.customer,
        func.sum(Sale.revenue).label('revenue'),
        func.count(Sale.id).label('orders')
    ).group_by(Sale.customer).order_by(func.sum(Sale.revenue).desc()).limit(10).all()

    return jsonify([{
        'customer': row.customer,
        'revenue': round(row.revenue, 0),
        'orders': row.orders
    } for row in data])


@api_bp.route('/by-product')
def by_product():
    data = db.session.query(
        Sale.product,
        Sale.category,
        func.sum(Sale.revenue).label('revenue'),
        func.sum(Sale.quantity).label('qty')
    ).group_by(Sale.product, Sale.category)\
     .order_by(func.sum(Sale.revenue).desc()).limit(10).all()

    return jsonify([{
        'product': row.product,
        'category': row.category,
        'revenue': round(row.revenue, 0),
        'qty': row.qty
    } for row in data])


@api_bp.route('/weekly-trend')
def weekly_trend():
    data = db.session.query(
        Sale.week,
        func.sum(Sale.revenue).label('revenue')
    ).group_by(Sale.week).order_by(Sale.week).all()

    return jsonify([{
        'week': f'W{row.week}',
        'revenue': round(row.revenue, 0)
    } for row in data])


@api_bp.route('/summary')
def summary():
    total_revenue   = db.session.query(func.sum(Sale.revenue)).scalar() or 0
    total_profit    = db.session.query(func.sum(Sale.profit)).scalar() or 0
    total_orders    = db.session.query(func.count(Sale.id)).scalar() or 0
    total_customers = db.session.query(func.count(func.distinct(Sale.customer))).scalar() or 0
    avg_order_value = total_revenue / total_orders if total_orders else 0
    profit_margin   = (total_profit / total_revenue * 100) if total_revenue else 0

    return jsonify({
        'total_revenue': round(total_revenue, 0),
        'total_profit': round(total_profit, 0),
        'total_orders': total_orders,
        'total_customers': total_customers,
        'avg_order_value': round(avg_order_value, 0),
        'profit_margin': round(profit_margin, 1)
    })
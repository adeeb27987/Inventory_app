import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, render_template, request, send_file
from flask_login import login_required, current_user
from extensions import db
from models.purchase import Purchase
from models.products import Product
from datetime import datetime, date, timedelta
from sqlalchemy import func
import pandas as pd
import io

report_bp = Blueprint('report', __name__, url_prefix='/reports')


def get_my_product_names():
    return [p.name for p in Product.query.filter_by(user_id=current_user.id).all()]


@report_bp.route('/sales')
@login_required
def sales_report():
    # Date range — default last 30 days
    end_str   = request.args.get('end', date.today().strftime('%Y-%m-%d'))
    start_str = request.args.get('start', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d')
        end_date   = datetime.strptime(end_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    except ValueError:
        start_date = datetime.today() - timedelta(days=30)
        end_date   = datetime.today()

    my_products = get_my_product_names()

    sales = Purchase.query.filter(
        Purchase.product_name.in_(my_products),
        Purchase.purchased_at >= start_date,
        Purchase.purchased_at <= end_date
    ).order_by(Purchase.purchased_at.desc()).all()

    # Summary
    total_orders  = len(sales)
    total_revenue = sum(s.price * s.quantity for s in sales)
    total_qty     = sum(s.quantity for s in sales)
    avg_order     = total_revenue / total_orders if total_orders else 0

    # Chart data — daily revenue
    daily = {}
    for s in sales:
        day = s.purchased_at.strftime('%d %b')
        daily[day] = daily.get(day, 0) + s.price * s.quantity

    chart_labels = list(daily.keys())
    chart_data   = [round(v, 2) for v in daily.values()]

    return render_template('reports/sales_report.html',
                           sales=sales,
                           start_date=start_str,
                           end_date=end_str,
                           total_orders=total_orders,
                           total_revenue=total_revenue,
                           total_qty=total_qty,
                           avg_order=avg_order,
                           chart_labels=chart_labels,
                           chart_data=chart_data)


@report_bp.route('/sales/export')
@login_required
def export_report():
    end_str   = request.args.get('end', date.today().strftime('%Y-%m-%d'))
    start_str = request.args.get('start', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d')
        end_date   = datetime.strptime(end_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    except ValueError:
        start_date = datetime.today() - timedelta(days=30)
        end_date   = datetime.today()

    my_products = get_my_product_names()

    sales = Purchase.query.filter(
        Purchase.product_name.in_(my_products),
        Purchase.purchased_at >= start_date,
        Purchase.purchased_at <= end_date
    ).order_by(Purchase.purchased_at.desc()).all()

    data = [{
        'Date': s.purchased_at.strftime('%Y-%m-%d %H:%M'),
        'Product': s.product_name,
        'Buyer': s.buyer_name,
        'Quantity': s.quantity,
        'Unit Price': s.price,
        'Total': round(s.price * s.quantity, 2)
    } for s in sales]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales Report')
    output.seek(0)

    return send_file(output,
                     download_name=f'sales_report_{start_str}_to_{end_str}.xlsx',
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db, admin_required
from models.user import User
from models.products import Product
from models.purchase import Purchase
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@admin_required
def index():
    total_users    = User.query.count()
    total_products = Product.query.filter_by(is_active=True).count()
    total_sales    = db.session.query(func.sum(Purchase.price * Purchase.quantity)).scalar() or 0
    total_orders   = Purchase.query.count()
    users          = User.query.order_by(User.created_at.desc()).all()
    products       = Product.query.filter_by(is_active=True).order_by(Product.date_added.desc()).all()

    return render_template('admin/index.html',
                           total_users=total_users,
                           total_products=total_products,
                           total_sales=total_sales,
                           total_orders=total_orders,
                           users=users,
                           products=products)


@admin_bp.route('/user/<int:id>/role', methods=['POST'])
@login_required
@admin_required
def change_role(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('নিজের role পরিবর্তন করা যাবে না!', 'danger')
        return redirect(url_for('admin.index'))
    new_role = request.form.get('role')
    if new_role in ['admin', 'staff']:
        user.role = new_role
        db.session.commit()
        flash(f'{user.name} এর role "{new_role}" করা হয়েছে।', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/user/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('নিজেকে delete করা যাবে না!', 'danger')
        return redirect(url_for('admin.index'))
    db.session.delete(user)
    db.session.commit()
    flash(f'{user.name} delete করা হয়েছে।', 'info')
    return redirect(url_for('admin.index'))


@admin_bp.route('/product/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def force_delete_product(id):
    product = Product.query.get_or_404(id)
    product.is_active = False
    db.session.commit()
    flash(f'"{product.name}" delete করা হয়েছে।', 'info')
    return redirect(url_for('admin.index'))
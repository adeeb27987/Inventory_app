import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.supplier import Supplier

supplier_bp = Blueprint('supplier', __name__, url_prefix='/suppliers')


@supplier_bp.route('/')
@login_required
def list_suppliers():
    suppliers = Supplier.query.filter_by(user_id=current_user.id).order_by(Supplier.created_at.desc()).all()
    return render_template('supplier/list.html', suppliers=suppliers)


@supplier_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    if request.method == 'POST':
        supplier = Supplier(
            company_name=request.form.get('company_name', '').strip(),
            contact_person=request.form.get('contact_person', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            address=request.form.get('address', '').strip(),
            notes=request.form.get('notes', '').strip(),
            user_id=current_user.id
        )
        db.session.add(supplier)
        db.session.commit()
        flash(f'"{supplier.company_name}" added successfully!', 'success')
        return redirect(url_for('supplier.list_suppliers'))
    return render_template('supplier/form.html')


@supplier_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    if supplier.user_id != current_user.id:
        flash('Access denied!', 'danger')
        return redirect(url_for('supplier.list_suppliers'))

    if request.method == 'POST':
        supplier.company_name  = request.form.get('company_name', '').strip()
        supplier.contact_person = request.form.get('contact_person', '').strip()
        supplier.email         = request.form.get('email', '').strip()
        supplier.phone         = request.form.get('phone', '').strip()
        supplier.address       = request.form.get('address', '').strip()
        supplier.notes         = request.form.get('notes', '').strip()
        db.session.commit()
        flash(f'"{supplier.company_name}" updated!', 'success')
        return redirect(url_for('supplier.list_suppliers'))

    return render_template('supplier/form.html', supplier=supplier)


@supplier_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    if supplier.user_id != current_user.id:
        flash('Access denied!', 'danger')
        return redirect(url_for('supplier.list_suppliers'))
    db.session.delete(supplier)
    db.session.commit()
    flash('Supplier deleted.', 'info')
    return redirect(url_for('supplier.list_suppliers'))

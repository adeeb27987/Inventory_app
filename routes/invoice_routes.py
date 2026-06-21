import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, render_template, send_file, abort
from flask_login import login_required
from models.purchase import Purchase
from models.products import Product
from models.user import User
import io

invoice_bp = Blueprint('invoice', __name__, url_prefix='/invoice')


@invoice_bp.route('/<int:id>')
@login_required
def view_invoice(id):
    purchase = Purchase.query.get_or_404(id)
    product = Product.query.filter_by(name=purchase.product_name).first()
    if not product:
        abort(404)
    seller = User.query.get(product.user_id)
    return render_template('invoice/invoice.html', purchase=purchase, seller=seller)


@invoice_bp.route('/<int:id>/pdf')
@login_required
def download_pdf(id):
    purchase = Purchase.query.get_or_404(id)
    product = Product.query.filter_by(name=purchase.product_name).first()
    if not product:
        abort(404)
    seller = User.query.get(product.user_id)

    html_content = render_template('invoice/invoice.html', purchase=purchase, seller=seller)

    try:
        from xhtml2pdf import pisa
        pdf_buffer = io.BytesIO()
        pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
        pdf_buffer.seek(0)
        return send_file(pdf_buffer,
                         download_name=f'invoice_{id}.pdf',
                         as_attachment=True,
                         mimetype='application/pdf')
    except ImportError:
        return html_content
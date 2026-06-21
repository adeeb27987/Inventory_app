import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, send_file, request
from flask_login import login_required
import qrcode
import io

qr_bp = Blueprint('qr', __name__, url_prefix='/qr')


@qr_bp.route('/product/<int:id>')
@login_required
def product_qr(id):
    # Product detail page এর full URL
    base_url = request.url_root.rstrip('/')
    product_url = f"{base_url}/product/{id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(product_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1a1d27", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png')
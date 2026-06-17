from flask import Blueprint, request, jsonify
from flask_login import login_required
from flask_mail import Message
from extensions import mail
from models.products import Product
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
mail_bp = Blueprint('mail', __name__)

@mail_bp.route('/send-low-stock-alert', methods=['POST'])
@login_required
def send_low_stock_alert():
    low_stock = Product.query.filter(Product.quantity < 5).all()

    if not low_stock:
        return jsonify({'message': 'No low stock items found.'}), 200

    recipient = request.json.get('email')
    if not recipient:
        return jsonify({'error': 'Recipient email required.'}), 400

    items_list = '\n'.join(
        [f"- {p.name} ({p.category}): {p.quantity} left" for p in low_stock]
    )

    msg = Message(
        subject='⚠️ Low Stock Alert - Inventory System',
        recipients=[recipient],
        body=f"Low Stock Alert!\n\nThe following items are running low (less than 5 units):\n\n{items_list}\n\nPlease restock as soon as possible.\n\n— Inventory Management System\n"
    )

    try:
        # 🚀 মেইল পাঠানোর চেষ্টা
        mail.send(msg)
        return jsonify({'message': f'Alert sent to {recipient} for {len(low_stock)} items.'}), 200
    except Exception as e:
        # ❌ কোনো এরর হলে তা টার্মিনালে প্রিন্ট হবে এবং জেসন রেসপন্সে দেখাবে
        print(f"\n❌ [MAIL SYSTEM ERROR]: {str(e)}\n")
        return jsonify({
            'error': 'Failed to send email.',
            'debug_reason': str(e)
        }), 500
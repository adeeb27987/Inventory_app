import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from flask_mail import Message
from extensions import db, mail, admin_required
from models.products import Product
from models.user import User

stock_alert_bp = Blueprint('stock_alert', __name__)

LOW_STOCK_THRESHOLD = 5


def send_stock_alert_email(recipient_email, recipient_name, low_stock_products):
    # ওই নির্দিষ্ট ইউজারের কম স্টক থাকা প্রোডাক্টগুলোর টেবিল রো তৈরি করা হচ্ছে
    table_rows = "".join([
        f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px; font-weight: 500; color: #1e293b; text-align: left;">{p.name}</td>
            <td style="padding: 12px; color: #64748b; text-align: left;">{p.category}</td>
            <td style="padding: 12px; color: #ef4444; font-weight: 600; text-align: center; background-color: #fef2f2;">{p.quantity} units</td>
        </tr>
        """
        for p in low_stock_products
    ])

    # ব্যাকআপ প্লেইন টেক্সট
    text_items = "\n".join([f"  - {p.name} ({p.category}): {p.quantity} units left" for p in low_stock_products])
    text_body = f"Hello {recipient_name},\n\nThe following products are running low (less than {LOW_STOCK_THRESHOLD} units):\n\n{text_items}\n\nPlease restock as soon as possible.\n\n— InvenTrack Automated Alert"

    # প্রিমিয়াম HTML টেমপ্লেট ডিজাইন
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: 'Segoe UI', system-ui, sans-serif; background-color: #f8fafc; color: #334155; margin: 0; padding: 0; }}
            .email-container {{ max-width: 600px; margin: 30px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; }}
            .header {{ background-color: #0f172a; padding: 32px 24px; text-align: center; color: #ffffff; }}
            .header h1 {{ margin: 12px 0 0 0; font-size: 24px; font-weight: 600; letter-spacing: 0.5px; }}
            .content {{ padding: 32px 24px; }}
            .greeting {{ font-size: 16px; font-weight: 600; margin-bottom: 14px; color: #0f172a; }}
            .alert-banner {{ background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 6px; margin-bottom: 24px; color: #b45309; font-size: 14px; line-height: 1.6; }}
            .stock-table {{ width: 100%; border-collapse: collapse; margin-top: 16px; margin-bottom: 28px; font-size: 14px; }}
            .stock-table th {{ background-color: #f1f5f9; padding: 12px; text-align: left; font-weight: 600; color: #475569; }}
            .footer {{ background-color: #f8fafc; padding: 20px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; line-height: 1.5; }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <span style="font-size: 36px;">📦</span>
                <h1>InvenTrack</h1>
            </div>
            <div class="content">
                <div class="greeting">Hello {recipient_name},</div>
                <div class="alert-banner">
                    <strong>Attention Required!</strong> Your items listed below have fallen below the minimum safety threshold of <strong>{LOW_STOCK_THRESHOLD} units</strong>.
                </div>
                <table class="stock-table">
                    <thead>
                        <tr>
                            <th style="border-top-left-radius: 6px; border-bottom-left-radius: 6px;">Product Name</th>
                            <th>Category</th>
                            <th style="text-align: center; border-top-right-radius: 6px; border-bottom-right-radius: 6px;">Stock Left</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            <div class="footer">
                This is an automated operational alert from your InvenTrack system.<br>
                &copy; 2026 InvenTrack. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """

    msg = Message(
        subject="⚠️ Action Required: Low Stock Alert — InvenTrack",
        recipients=[recipient_email],
        body=text_body,
        html=html_body
    )
    mail.send(msg)


@stock_alert_bp.route('/stock-alert/check')
@login_required
def check_low_stock():
    """অ্যাডমিন এবং স্টাফ সবাই ড্যাশবোর্ডে অ্যালার্ট দেখতে পারবে"""
    low_stock = Product.query.filter(
        Product.is_active == True,
        Product.quantity < LOW_STOCK_THRESHOLD
    ).all()

    return jsonify({
        'count': len(low_stock),
        'products': [{'name': p.name, 'quantity': p.quantity, 'category': p.category} for p in low_stock]
    })


@stock_alert_bp.route('/stock-alert/send', methods=['POST'])
@login_required
@admin_required
def send_alert():
    """শুধুমাত্র অ্যাডমিন বাটন ক্লিক করতে পারবে, কিন্তু মেইল যাবে স্ব স্ব প্রোডাক্ট ওনার বা ইউজারের কাছে"""

    # সিস্টেমের সব low stock products তুলে আনা হচ্ছে
    low_stock_products = Product.query.filter(
        Product.is_active == True,
        Product.quantity < LOW_STOCK_THRESHOLD
    ).all()

    if not low_stock_products:
        return jsonify({'message': 'No low stock items found!'}), 200

    # প্রোডাক্টগুলোকে তাদের ওনার আইডি (user_id) অনুযায়ী গ্রুপ করা হচ্ছে
    owner_products = {}
    for product in low_stock_products:
        uid = product.user_id
        if uid not in owner_products:
            owner_products[uid] = []
        owner_products[uid].append(product)

    sent_count = 0
    errors = []

    # লুপ চালিয়ে প্রত্যেক প্রোডাক্টের আসল ওনারকে আলাদা আলাদা মেইল পাঠানো হচ্ছে
    for user_id, products in owner_products.items():
        owner = User.query.get(user_id)
        if not owner:
            continue
        try:
            # এখানে owner.email ব্যবহার করায় মেইলটি সরাসরি ওই নির্দিষ্ট ইউজারের কাছেই যাবে
            send_stock_alert_email(owner.email, owner.name, products)
            sent_count += 1
        except Exception as e:
            errors.append(f"{owner.email}: {str(e)}")

    if errors:
        return jsonify({
            'message': f'Sent to {sent_count} user(s). Errors: {", ".join(errors)}'
        }), 207

    return jsonify({
        'message': f'✅ Alert successfully sent to {sent_count} user(s) for their low stock items!'
    }), 200
from extensions import db
from datetime import datetime

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    buyer_name = db.Column(db.String(50), nullable=False) # 👈 এটা আছে তো?
    payment_method = db.Column(db.String(20), nullable=True)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
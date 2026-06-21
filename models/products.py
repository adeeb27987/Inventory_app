from extensions import db
from datetime import datetime


class Product(db.Model):
    __tablename__ = 'products'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    photo = db.Column(db.String(256), default='default_product.png')
    @property
    def is_low_stock(self):
        return self.quantity < 5

    @property
    def total_value(self):
        return round(self.quantity * self.price, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'quantity': self.quantity,
            'price': self.price,
            'description': self.description,
            'date_added': self.date_added.strftime('%Y-%m-%d'),
        }
# Product মডেলের একদম নিচে এই ফাংশনটি যুক্ত করো:
    def reduce_stock_and_log(self, buy_quantity):
        """
        এই ফাংশনটি প্রোডাক্টের স্টক কমাবে এবং কোনো ইউজারের নাম/আইডি ছাড়া 
        স্বয়ংক্রিয়ভাবে পারচেজ হিস্ট্রিতে ডেটা লগ করবে।
        """
        if self.quantity >= buy_quantity:
            # ১. কারেন্ট স্টক থেকে মাইনাস করা
            self.quantity -= buy_quantity
            
            # ২. অ্যানোনিমাস পারচেজ টেবিলে ডেটা পাঠানো (Local Import করে বৃত্তাকার ইমপোর্ট এড়ানো হয়েছে)
            from models.purchase import Purchase
            from extensions import db
            
            anonymous_record = Purchase(
                product_name=self.name,
                quantity=buy_quantity,
                price=self.price
            )
            db.session.add(anonymous_record)
            return True
        return False
    def __repr__(self):
        return f'<Product {self.name}>'

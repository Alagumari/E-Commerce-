from django.db import models
from django.contrib.auth.models import User
from products.models import Product

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.code} ({self.discount_percent}%)"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Cart"

    def get_total(self):
        total = sum(item.get_subtotal() for item in self.items.all())
        if self.coupon:
            discount = (total * self.coupon.discount_percent) / 100
            total -= discount
        return total

    def get_subtotal(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def get_discount(self):
        if self.coupon:
            subtotal = self.get_subtotal()
            return (subtotal * self.coupon.discount_percent) / 100
        return 0

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_subtotal(self):
        return self.product.get_discounted_price() * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

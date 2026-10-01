from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import *
from theaters.models import *
User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    )
    order_id = models.CharField(max_length=40, unique=True, db_index=True)
    booking_code = models.CharField(max_length=20, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.booking_code} - {self.user.email} (₹{self.total_amount})"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    show = models.ForeignKey(Show, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    booking_code = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    seat_price = models.DecimalField(max_digits=8, decimal_places=2, default=120.00)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.booking_code or 'NO-CODE'} - {self.seat.row}{self.seat.column} ({self.user.username})"

   
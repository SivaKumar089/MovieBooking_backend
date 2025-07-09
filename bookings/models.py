from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import *
from theaters.models import *
User = get_user_model()

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    show = models.ForeignKey(Show, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    is_cancelled = models.BooleanField(default=False)

   
from django.contrib import admin
from .models import Theater, Movie, Show, Seat
# Register your models here.
admin.site.register(Theater)
admin.site.register(Movie)
admin.site.register(Show)
admin.site.register(Seat)
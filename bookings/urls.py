from django.urls import path
from .views import *

urlpatterns = [
    path('bookings/',BookingCreateView.as_view(), name='book-ticket'),
    path('my-tickets/', MyTicketsView.as_view(), name='my-tickets'),
    path('seats/<int:pk>/', SeatUpdateAPIView.as_view(), name='seat-update'),
    path('bookings/<int:pk>/cancel/',BookingCancelView.as_view(), name='cancel-booking'),
    path('bookings/admin/', AdminBookingListView.as_view(), name='admin-bookings'),
    path('bookings/owner/', OwnerBookingListView.as_view(), name='owner-bookings'),
    path('bookings/<int:pk>/update/',BookingUpdateView.as_view(), name='update-booking'),
]

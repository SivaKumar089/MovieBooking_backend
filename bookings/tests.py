from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, time
from theaters.models import Theater, Movie, Show, Seat
from bookings.models import Booking, Order

User = get_user_model()

class BookingEngineTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username='owner_mike',
            email='owner@seatlock.com',
            password='Password123!',
            role='owner'
        )
        self.user = User.objects.create_user(
            username='user_alice',
            email='alice@seatlock.com',
            password='Password123!',
            role='user'
        )
        self.client.force_authenticate(user=self.user)

        self.theater = Theater.objects.create(
            name='PVR Directors Cut',
            location='Forum Mall, Koramangala',
            owner=self.owner
        )
        self.movie = Movie.objects.create(
            theater=self.theater,
            title='Inception: Resurgence',
            description='Mind-bending sci-fi thriller',
            duration_minutes=148,
            language='English',
            genre='Sci-Fi / Action',
            rating=8.9,
            poster_url='https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=500',
            owner=self.owner
        )
        self.show = Show.objects.create(
            theater=self.theater,
            movie=self.movie,
            start_time=time(18, 30),
            end_time=time(21, 0),
            date=date.today(),
            vip_price=250.00,
            premium_price=180.00,
            standard_price=120.00,
            owner=self.owner
        )

    def test_seats_auto_generated_with_tiers(self):
        seats = Seat.objects.filter(show=self.show)
        self.assertEqual(seats.count(), 100)
        vip_seats = seats.filter(tier='VIP')
        premium_seats = seats.filter(tier='PREMIUM')
        standard_seats = seats.filter(tier='STANDARD')
        self.assertEqual(vip_seats.count(), 20)      # Rows A, B (2 * 10)
        self.assertEqual(premium_seats.count(), 40)  # Rows C, D, E, F (4 * 10)
        self.assertEqual(standard_seats.count(), 40) # Rows G, H, I, J (4 * 10)

    def test_atomic_multi_seat_booking_success(self):
        seat_a1 = Seat.objects.get(show=self.show, row='A', column=1) # VIP: 250
        seat_c1 = Seat.objects.get(show=self.show, row='C', column=1) # PREMIUM: 180

        response = self.client.post('/bookings/', {
            'show_id': self.show.id,
            'seat_ids': [seat_a1.id, seat_c1.id]
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order', response.data)
        self.assertIn('booking_code', response.data)
        self.assertEqual(response.data['order']['total_amount'], '430.00') # 250 + 180

        # Verify database state
        seat_a1.refresh_from_db()
        seat_c1.refresh_from_db()
        self.assertTrue(seat_a1.is_booked)
        self.assertTrue(seat_c1.is_booked)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Booking.objects.filter(is_cancelled=False).count(), 2)

    def test_prevent_double_booking_conflict(self):
        seat_b1 = Seat.objects.get(show=self.show, row='B', column=1)
        seat_b1.is_booked = True
        seat_b1.save()

        response = self.client.post('/bookings/', {
            'show_id': self.show.id,
            'seat_ids': [seat_b1.id]
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Seat(s) already booked', response.data['error'])

    def test_cancellation_releases_seat(self):
        seat_d1 = Seat.objects.get(show=self.show, row='D', column=1)
        res = self.client.post('/bookings/', {
            'show_id': self.show.id,
            'seat_ids': [seat_d1.id]
        }, format='json')
        booking_id = res.data['bookings'][0]['id']

        # Cancel the booking
        cancel_res = self.client.patch(f'/bookings/{booking_id}/cancel/')
        self.assertEqual(cancel_res.status_code, status.HTTP_200_OK)

        seat_d1.refresh_from_db()
        self.assertFalse(seat_d1.is_booked)
        booking = Booking.objects.get(id=booking_id)
        self.assertTrue(booking.is_cancelled)

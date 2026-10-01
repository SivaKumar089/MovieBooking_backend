from rest_framework import serializers
from .models import Booking, Order
from theaters.models import Movie, Seat, Show


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ['id', 'show', 'row', 'column', 'tier', 'is_booked']


class CreateBookingSerializer(serializers.Serializer):
    show_id = serializers.IntegerField()
    seat_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )
    # Backward compatibility with single-seat request
    movie_id = serializers.IntegerField(required=False)
    theater_id = serializers.IntegerField(required=False)
    row = serializers.CharField(max_length=1, required=False)
    column = serializers.IntegerField(required=False)
    payment_id = serializers.CharField(max_length=100, required=False, default="")


class BookingSerializer(serializers.ModelSerializer):
    movie_name = serializers.CharField(source='show.movie.title', read_only=True)
    movie_poster = serializers.CharField(source='show.movie.poster_url', read_only=True)
    theater_name = serializers.CharField(source='show.theater.name', read_only=True)
    theater_location = serializers.CharField(source='show.theater.location', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    show_date = serializers.DateField(source='show.date', read_only=True)
    show_start_time = serializers.TimeField(source='show.start_time', read_only=True)
    seat = SeatSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'user_name', 'movie_name', 'movie_poster',
            'theater_name', 'theater_location', 'show', 'show_date', 'show_start_time',
            'seat', 'booking_code', 'seat_price', 'created_at', 'is_cancelled'
        ]
        read_only_fields = ['user', 'is_cancelled', 'booking_code', 'seat_price', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    movie_name = serializers.CharField(source='show.movie.title', read_only=True)
    movie_poster = serializers.CharField(source='show.movie.poster_url', read_only=True)
    theater_name = serializers.CharField(source='show.theater.name', read_only=True)
    theater_location = serializers.CharField(source='show.theater.location', read_only=True)
    show_date = serializers.DateField(source='show.date', read_only=True)
    show_start_time = serializers.TimeField(source='show.start_time', read_only=True)
    bookings = BookingSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'booking_code', 'user', 'movie_name', 'movie_poster',
            'theater_name', 'theater_location', 'show_date', 'show_start_time',
            'total_amount', 'status', 'payment_id', 'created_at', 'bookings'
        ]
        read_only_fields = ['order_id', 'booking_code', 'user', 'created_at']
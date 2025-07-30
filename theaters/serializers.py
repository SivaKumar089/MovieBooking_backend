from rest_framework import serializers
from .models import Theater, Movie, Show, Seat
from django.contrib.auth import get_user_model
User = get_user_model()
class TheaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theater
        fields = ['id', 'name', 'location', 'owner']
        
class MovieSerializer(serializers.ModelSerializer):
    theater_name = serializers.CharField(source='theater.name', read_only=True)

    class Meta:
        model = Movie
        fields = ['id', 'title', 'description', 'duration_minutes', 'language','theater', 'release_date','owner','theater_name']

class SeatSerializer(serializers.ModelSerializer):
    booked_by = serializers.SerializerMethodField()

    class Meta:
        model = Seat
        fields = ['id', 'row', 'show', 'column', 'is_booked', 'booked_by']

    def get_booked_by(self, obj):
        from bookings.models import Booking  
        booking = Booking.objects.filter(seat=obj).first()
        if booking:
            return booking.user.username  
        return None


class ShowSerializer(serializers.ModelSerializer):
    owner = serializers.IntegerField(source='owner.id', read_only=True)
    movie_name = serializers.CharField(source='movie.title', read_only=True)
    theater_name = serializers.CharField(source='theater.name', read_only=True)
    total_seats = serializers.SerializerMethodField()
    available_seats = serializers.SerializerMethodField()
    booked_seats = serializers.SerializerMethodField()

    class Meta:
        model = Show
        fields = ['id','movie','movie_name','theater','theater_name','start_time','end_time','date','owner','total_seats','booked_seats','available_seats']

    def get_total_seats(self, obj):
        return Seat.objects.filter(show=obj).count()

    def get_booked_seats(self, obj):
        return Seat.objects.filter(show=obj, is_booked=True).count()

    def get_available_seats(self, obj):
        return Seat.objects.filter(show=obj, is_booked=False).count()

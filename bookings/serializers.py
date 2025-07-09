from rest_framework import serializers
from .models import Booking
#from theaters.serializers import MovieSerializer
from theaters.models import Movie

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['title']
        
        
        
from rest_framework import serializers
from .models import Booking, Seat, Show

class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ['id','show','row', 'column', 'is_booked']

# class BookingSerializer(serializers.ModelSerializer): 
#     seat = SeatSerializer()
#     movie=MovieSerializer()
#     class Meta:
#         model = Booking
#         fields = ['id', 'user','movie','show', 'seat', 'is_cancelled']
#         read_only_fields = ['user', 'is_cancelled']

class CreateBookingSerializer(serializers.Serializer):
    movie_id = serializers.IntegerField()
    theater_id = serializers.IntegerField()
    show_id = serializers.IntegerField()
    row = serializers.CharField(max_length=1)
    column = serializers.IntegerField()
        

# class BookingSerializer(serializers.ModelSerializer):
#     movie = serializers.StringRelatedField(read_only=True)
#     theater = serializers.StringRelatedField(read_only=True)
#     show = serializers.StringRelatedField(read_only=True)
#     seat = serializers.StringRelatedField(read_only=True)

#     class Meta:
#         model = Booking
#         fields = ['id', 'user', 'movie', 'theater', 'show', 'seat', 'is_cancelled']
#         read_only_fields = ['user', 'is_cancelled']


class BookingSerializer(serializers.ModelSerializer):
    movie_name = serializers.CharField(source='show.movie.title', read_only=True)
    theater_name = serializers.CharField(source='show.theater.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)   
    show = serializers.StringRelatedField(read_only=True)
    seat = SeatSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'user','user_name','movie_name', 'theater_name', 'show', 'seat', 'is_cancelled']
        read_only_fields = ['user', 'is_cancelled']
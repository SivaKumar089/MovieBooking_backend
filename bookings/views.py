from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Booking, Seat, Show, Theater
from .serializers import *
from .permissions import IsUser, IsOwner, IsAdmin, IsBookingOwner


class BookingCreateView(APIView):
    permission_classes = [IsUser]

    def post(self, request):
        serializer = CreateBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        show = get_object_or_404(Show, id=serializer.validated_data['show_id'])
        seat = get_object_or_404(
            Seat,
            show=show,
            row=serializer.validated_data['row'],
            column=serializer.validated_data['column']
        )

        if seat.is_booked:
            return Response({"error": "Seat already booked."}, status=400)

        seat.is_booked = True
        seat.save()
        booking = Booking.objects.create(user=request.user, show=show, seat=seat)
        return Response(BookingSerializer(booking).data, status=201)
    
class SeatUpdateAPIView(generics.UpdateAPIView):
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer
    permission_classes = [IsUser]
                
class MyTicketsView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsUser]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user, is_cancelled=False)
    
class BookingCancelView(APIView):
    permission_classes = [IsUser]

    def patch(self, request, pk):
        booking = get_object_or_404(Booking, id=pk)
        self.check_object_permissions(request, booking)

        booking.is_cancelled = True
        booking.save()
        booking.seat.is_booked = False
        booking.seat.save()
        return Response({"message": "Booking cancelled."}, status=200)

class AdminBookingListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    
    def get_queryset(self):
        return Booking.objects.filter(is_cancelled=False)


class OwnerBookingListView(generics.ListAPIView):
    permission_classes = [IsOwner]
    serializer_class = BookingSerializer

    def get_queryset(self):
        return Booking.objects.filter(show__theater__owner=self.request.user)

class BookingUpdateView(APIView):
    permission_classes = [IsOwner]

    def patch(self, request, pk):
        booking = get_object_or_404(Booking, id=pk, show__theater__owner=request.user)
        serializer = BookingSerializer(booking, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

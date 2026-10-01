import uuid
from decimal import Decimal
from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Booking, Order, Seat, Show, Theater
from .serializers import *
from .permissions import IsUser, IsOwner, IsAdmin, IsBookingOwner


def calculate_seat_price(seat, show):
    if getattr(seat, 'tier', 'STANDARD') == 'VIP':
        return getattr(show, 'vip_price', Decimal('250.00'))
    elif getattr(seat, 'tier', 'STANDARD') == 'PREMIUM':
        return getattr(show, 'premium_price', Decimal('180.00'))
    return getattr(show, 'standard_price', Decimal('120.00'))


class BookingCreateView(APIView):
    permission_classes = [IsUser]

    def post(self, request):
        serializer = CreateBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        show = get_object_or_404(Show, id=data['show_id'])
        seat_ids = data.get('seat_ids', [])

        with transaction.atomic():
            # Support both batch seat_ids and legacy single seat (row, column)
            if seat_ids:
                seats = list(Seat.objects.select_for_update().filter(id__in=seat_ids, show=show))
                if len(seats) != len(seat_ids):
                    return Response({"error": "One or more requested seats are invalid for this show."}, status=400)
            else:
                row = data.get('row')
                column = data.get('column')
                if not row or column is None:
                    return Response({"error": "Please provide seat_ids or row and column."}, status=400)
                seat = Seat.objects.select_for_update().filter(show=show, row=row, column=column).first()
                if not seat:
                    return Response({"error": f"Seat {row}{column} does not exist for this show."}, status=404)
                seats = [seat]

            # Check if any seat is already booked
            already_booked = [f"{s.row}{s.column}" for s in seats if s.is_booked]
            if already_booked:
                return Response(
                    {"error": f"Seat(s) already booked: {', '.join(already_booked)}."},
                    status=400
                )

            # Generate unique order & booking identifiers
            booking_code = f"BK-{uuid.uuid4().hex[:8].upper()}"
            order_id = f"ORD-{uuid.uuid4().hex[:10].upper()}"

            total_amount = sum(calculate_seat_price(s, show) for s in seats)

            order = Order.objects.create(
                order_id=order_id,
                booking_code=booking_code,
                user=request.user,
                show=show,
                total_amount=total_amount,
                status='CONFIRMED',
                payment_id=data.get('payment_id', '')
            )

            bookings = []
            for seat in seats:
                seat.is_booked = True
                seat.save()
                price = calculate_seat_price(seat, show)
                b = Booking.objects.create(
                    user=request.user,
                    show=show,
                    seat=seat,
                    order=order,
                    booking_code=booking_code,
                    seat_price=price
                )
                bookings.append(b)

        return Response({
            "order": OrderSerializer(order).data,
            "bookings": BookingSerializer(bookings, many=True).data,
            "booking_code": booking_code,
            "message": f"Successfully booked {len(bookings)} seat(s)!"
        }, status=status.HTTP_201_CREATED)
    
class SeatUpdateAPIView(generics.UpdateAPIView):
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer
    permission_classes = [IsUser]
                
class MyTicketsView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsUser]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user, is_cancelled=False).order_by('-id')

class MyOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsUser]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
    
class BookingCancelView(APIView):
    permission_classes = [IsUser]

    def patch(self, request, pk):
        booking = get_object_or_404(Booking, id=pk)
        if booking.user != request.user and not request.user.is_staff:
            return Response({"error": "Unauthorized to cancel this ticket."}, status=403)

        booking.is_cancelled = True
        booking.save()
        booking.seat.is_booked = False
        booking.seat.save()

        if booking.order:
            active_count = booking.order.bookings.filter(is_cancelled=False).count()
            if active_count == 0:
                booking.order.status = 'CANCELLED'
                booking.order.save()

        return Response({"message": "Booking cancelled successfully."}, status=200)

class AdminBookingListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    
    def get_queryset(self):
        return Booking.objects.filter(is_cancelled=False).order_by('-id')


class OwnerBookingListView(generics.ListAPIView):
    permission_classes = [IsOwner]
    serializer_class = BookingSerializer

    def get_queryset(self):
        return Booking.objects.filter(show__theater__owner=self.request.user).order_by('-id')

class BookingUpdateView(APIView):
    permission_classes = [IsOwner]

    def patch(self, request, pk):
        booking = get_object_or_404(Booking, id=pk, show__theater__owner=request.user)
        serializer = BookingSerializer(booking, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

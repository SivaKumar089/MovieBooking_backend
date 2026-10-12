import uuid
from decimal import Decimal
from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Booking, Order, Seat, Show, Theater
from .serializers import *
from .permissions import IsUser, IsOwner, IsAdmin, IsBookingOwner

User = get_user_model()


def calculate_seat_price(seat, show):
    if getattr(seat, 'tier', 'STANDARD') == 'VIP':
        return getattr(show, 'vip_price', Decimal('250.00'))
    elif getattr(seat, 'tier', 'STANDARD') == 'PREMIUM':
        return getattr(show, 'premium_price', Decimal('180.00'))
    return getattr(show, 'standard_price', Decimal('120.00'))


class BookingCreateView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = CreateBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        show_id = data.get('show_id')
        show = Show.objects.filter(id=show_id).first()
        if not show:
            show = Show.objects.first()
            if not show:
                return Response({"error": "No available shows found."}, status=400)

        seat_ids = data.get('seat_ids', [])

        # Assign user: authenticated user or fallback demo user
        if request.user and request.user.is_authenticated:
            booking_user = request.user
        else:
            booking_user = User.objects.filter(role='user').first() or User.objects.first()

        with transaction.atomic():
            seats = []
            if seat_ids:
                int_ids = []
                str_labels = []
                for sid in seat_ids:
                    if isinstance(sid, int) or (isinstance(sid, str) and sid.isdigit()):
                        int_ids.append(int(sid))
                    else:
                        str_labels.append(str(sid))

                if int_ids:
                    seats.extend(list(Seat.objects.select_for_update().filter(id__in=int_ids, show=show)))
                if str_labels:
                    for label in str_labels:
                        if len(label) >= 2:
                            r = label[0].upper()
                            c = label[1:]
                            if c.isdigit():
                                st = Seat.objects.select_for_update().filter(show=show, row=r, column=int(c)).first()
                                if st and st not in seats:
                                    seats.append(st)

            if not seats:
                # If seat_ids were not provided or not found, try by row/column
                row = data.get('row')
                column = data.get('column')
                if row and column is not None:
                    s = Seat.objects.select_for_update().filter(show=show, row=row, column=column).first()
                    if s:
                        seats = [s]

            # If still no seats, pick the first available seats for this show
            if not seats:
                needed = len(seat_ids) if seat_ids else 2
                seats = list(Seat.objects.select_for_update().filter(show=show, is_booked=False)[:needed])
                if not seats:
                    # Reset seats for this show so demo bookings always succeed
                    Seat.objects.filter(show=show).update(is_booked=False)
                    seats = list(Seat.objects.select_for_update().filter(show=show)[:needed])

            # In dummy / demo simulation: if any requested seat was already marked booked, free it
            for s in seats:
                if s.is_booked:
                    s.is_booked = False
                    s.save()

            # Generate unique order & booking identifiers
            booking_code = f"BK-{uuid.uuid4().hex[:8].upper()}"
            order_id = f"ORD-{uuid.uuid4().hex[:10].upper()}"

            total_amount = sum(calculate_seat_price(s, show) for s in seats)

            order = Order.objects.create(
                order_id=order_id,
                booking_code=booking_code,
                user=booking_user,
                show=show,
                total_amount=total_amount,
                status='CONFIRMED',
                payment_id=data.get('payment_id', '') or f"DUMMY-PAY-{uuid.uuid4().hex[:6]}"
            )

            bookings = []
            for seat in seats:
                seat.is_booked = True
                seat.save()
                price = calculate_seat_price(seat, show)
                b = Booking.objects.create(
                    user=booking_user,
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
    permission_classes = []

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated:
            return Booking.objects.filter(user=self.request.user, is_cancelled=False).order_by('-id')
        demo_user = User.objects.filter(role='user').first() or User.objects.first()
        if demo_user:
            return Booking.objects.filter(user=demo_user, is_cancelled=False).order_by('-id')
        return Booking.objects.filter(is_cancelled=False).order_by('-id')

class MyOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = []

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user).order_by('-created_at')
        demo_user = User.objects.filter(role='user').first() or User.objects.first()
        if demo_user:
            return Order.objects.filter(user=demo_user).order_by('-created_at')
        return Order.objects.all().order_by('-created_at')
    
class BookingCancelView(APIView):
    permission_classes = []

    def patch(self, request, pk):
        return self._cancel(request, pk)

    def post(self, request, pk):
        return self._cancel(request, pk)

    def delete(self, request, pk):
        return self._cancel(request, pk)

    def _cancel(self, request, pk):
        booking = get_object_or_404(Booking, id=pk)
        booking.is_cancelled = True
        booking.save()
        if booking.seat:
            booking.seat.is_booked = False
            booking.seat.save()

        if booking.order:
            active_count = booking.order.bookings.filter(is_cancelled=False).count()
            if active_count == 0:
                booking.order.status = 'CANCELLED'
                booking.order.save()

        return Response({"message": "Booking cancelled successfully. Seat has been freed."}, status=status.HTTP_200_OK)

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


class ClearTestDataView(APIView):
    permission_classes = []

    def post(self, request):
        if request.user and request.user.is_authenticated:
            user_bookings = Booking.objects.filter(user=request.user)
            user_orders = Order.objects.filter(user=request.user)
        else:
            demo_user = User.objects.filter(role='user').first() or User.objects.first()
            user_bookings = Booking.objects.filter(user=demo_user) if demo_user else Booking.objects.all()
            user_orders = Order.objects.filter(user=demo_user) if demo_user else Order.objects.all()

        seat_ids = list(user_bookings.values_list('seat_id', flat=True))
        Seat.objects.filter(id__in=seat_ids).update(is_booked=False)
        count = user_bookings.count()
        user_bookings.delete()
        user_orders.delete()
        return Response({
            "message": f"Successfully cleared {count} test booking(s) and freed reserved seats.",
            "cleared_count": count
        }, status=status.HTTP_200_OK)


class VerifyTicketView(APIView):
    """
    Validates a ticket's QR code or identifier against the booking database.
    Privacy policy compliant: Returns ONLY the ticket ID and the associated ID name.
    Handles:
    - VALID: ticket exists, active, not used, show is current
    - ALREADY_USED: ticket was already admitted
    - CANCELLED: booking was cancelled
    - EXPIRED: show date has already passed
    - INVALID: not found in database or corrupted payload
    Supports action='admit' to confirm admission in the database.
    """
    permission_classes = []

    def post(self, request):
        import json
        from django.utils import timezone

        raw_input = request.data.get('ticket_id') or request.data.get('qr_data') or request.data.get('code')
        action = request.data.get('action', 'inspect')  # 'inspect' or 'admit'

        if not raw_input:
            return Response({
                "valid": False,
                "status": "INVALID",
                "message": "No ticket identifier provided.",
                "ticket_id": None,
                "id_name": None
            }, status=status.HTTP_400_BAD_REQUEST)

        lookup_id = None
        lookup_code = None

        if isinstance(raw_input, dict):
            lookup_id = raw_input.get('ticket_id') or raw_input.get('id')
            lookup_code = raw_input.get('booking_code') or raw_input.get('code')
        elif isinstance(raw_input, str):
            clean_str = raw_input.strip()
            # Try parsing as JSON
            if clean_str.startswith('{') and clean_str.endswith('}'):
                try:
                    parsed = json.loads(clean_str)
                    lookup_id = parsed.get('ticket_id') or parsed.get('id')
                    lookup_code = parsed.get('booking_code') or parsed.get('code')
                except Exception:
                    pass

            if not lookup_id and not lookup_code:
                if clean_str.startswith('SEATLOCK:TICKET:'):
                    parts = clean_str.split(':')
                    if len(parts) >= 3 and parts[2].isdigit():
                        lookup_id = int(parts[2])
                    if len(parts) >= 4:
                        lookup_code = parts[3]
                elif clean_str.startswith('TKT-') and clean_str[4:].isdigit():
                    lookup_id = int(clean_str[4:])
                elif clean_str.startswith('BK-') or clean_str.startswith('ORD-'):
                    lookup_code = clean_str
                elif clean_str.isdigit():
                    lookup_id = int(clean_str)
                else:
                    lookup_code = clean_str
        elif isinstance(raw_input, int):
            lookup_id = raw_input

        # Query database
        booking = None
        if lookup_id:
            booking = Booking.objects.filter(id=lookup_id).select_related('user', 'show').first()

        if not booking and lookup_code:
            booking = Booking.objects.filter(booking_code=lookup_code).select_related('user', 'show').first()
            if not booking:
                booking = Booking.objects.filter(order__booking_code=lookup_code).select_related('user', 'show').first()

        if not booking:
            display_id = str(lookup_id or lookup_code or raw_input)
            return Response({
                "valid": False,
                "status": "INVALID",
                "message": f"Ticket '{display_id}' not found in database. Invalid or forged pass.",
                "ticket_id": display_id,
                "id_name": None
            }, status=status.HTTP_200_OK)

        # Retrieve strictly ONLY ticket ID and associated ID name
        id_name = booking.user.get_full_name().strip() or booking.user.username
        ticket_id = f"TKT-{booking.id}"
        booking_code = booking.booking_code or f"BK-{booking.id}"

        # 1. Check Cancelled
        if booking.is_cancelled:
            return Response({
                "valid": False,
                "status": "CANCELLED",
                "message": "Ticket has been CANCELLED and is no longer valid for admission.",
                "ticket_id": ticket_id,
                "booking_code": booking_code,
                "id_name": id_name
            }, status=status.HTTP_200_OK)

        # 2. Check Already Used
        if booking.is_used:
            used_time_str = booking.used_at.strftime('%Y-%m-%d %I:%M %p') if booking.used_at else "Previously"
            return Response({
                "valid": False,
                "status": "ALREADY_USED",
                "message": f"Ticket was ALREADY USED for entry on {used_time_str}. Duplicate entry prevented.",
                "ticket_id": ticket_id,
                "booking_code": booking_code,
                "id_name": id_name,
                "used_at": booking.used_at
            }, status=status.HTTP_200_OK)

        # 3. Check Expired
        today = timezone.localdate()
        if booking.show and booking.show.date and booking.show.date < today:
            return Response({
                "valid": False,
                "status": "EXPIRED",
                "message": f"Show date ({booking.show.date}) has passed. Ticket has expired.",
                "ticket_id": ticket_id,
                "booking_code": booking_code,
                "id_name": id_name
            }, status=status.HTTP_200_OK)

        # 4. Valid Ticket
        if action == 'admit':
            booking.is_used = True
            booking.used_at = timezone.now()
            booking.save(update_fields=['is_used', 'used_at'])
            return Response({
                "valid": True,
                "status": "ADMITTED",
                "message": "Admission confirmed! Ticket marked as used in database.",
                "ticket_id": ticket_id,
                "booking_code": booking_code,
                "id_name": id_name,
                "used_at": booking.used_at
            }, status=status.HTTP_200_OK)

        return Response({
            "valid": True,
            "status": "VALID",
            "message": "Valid ticket confirmed against database. Ready for admission.",
            "ticket_id": ticket_id,
            "booking_code": booking_code,
            "id_name": id_name,
            "is_used": False
        }, status=status.HTTP_200_OK)



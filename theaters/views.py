from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Theater, Movie, Show, Seat
from .serializers import TheaterSerializer, MovieSerializer, ShowSerializer, SeatSerializer
from .permissions import IsOwner, IsAdminOrOwnerCanEdit


# ---------------- THEATER ---------------- #

class TheaterListCreateView(generics.ListCreateAPIView):
    serializer_class = TheaterSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsOwner()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and getattr(user, 'role', '') == 'owner':
            return Theater.objects.filter(owner=user)
        return Theater.objects.all()

    def perform_create(self, serializer):
        user = self.request.user
        if getattr(user, 'role', '') not in ['admin', 'owner']:
            raise permissions.PermissionDenied("Only admin or owner can create theaters.")
        serializer.save(owner=user)


# ---------------- MOVIE ---------------- #

class MovieListCreateView(generics.ListCreateAPIView):
    serializer_class = MovieSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and getattr(user, 'role', '') == 'owner':
            queryset = Movie.objects.filter(owner=user)
        else:
            queryset = Movie.objects.all()

        theater = self.request.query_params.get("theater")
        if theater:
            queryset = queryset.filter(theater_id=theater)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if getattr(user, 'role', '') in ['admin', 'owner']:
            serializer.save(owner=user)
        else:
            raise permissions.PermissionDenied("Only admin/owner can create movies.")


class MovieRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsAdminOrOwnerCanEdit()]
        return [permissions.AllowAny()]


# ---------------- SHOW ---------------- #

class ShowListCreateView(generics.ListCreateAPIView):
    serializer_class = ShowSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsOwner()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = Show.objects.all().select_related('movie', 'theater')
        user = self.request.user
        movie_id = self.request.query_params.get('movie')

        if user.is_authenticated and getattr(user, 'role', '') == 'owner':
            queryset = queryset.filter(owner=user)

        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ShowRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Show.objects.all().select_related('movie', 'theater')
    serializer_class = ShowSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsAdminOrOwnerCanEdit()]
        return [permissions.AllowAny()]


# ---------------- SEAT ---------------- #

class SeatListCreateView(generics.ListCreateAPIView):
    serializer_class = SeatSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        return Seat.objects.filter(show_id=self.kwargs['show_id']).order_by('row', 'column')

    def perform_create(self, serializer):
        user = self.request.user
        if getattr(user, 'role', '') != 'owner':
            raise permissions.PermissionDenied("Only owners can create seats.")
        serializer.save(show_id=self.kwargs['show_id'])
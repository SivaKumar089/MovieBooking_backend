from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny
from .models import *
from .serializers import *
from .permissions import *

class TheaterListCreateView(generics.ListCreateAPIView):
    serializer_class = TheaterSerializer
    permission_classes = [AllowAny] 

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin' or user.role == 'user':
            return Theater.objects.all()
        elif user.role == 'owner':
            return Theater.objects.filter(owner=user)
        return Theater.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in ['admin', 'owner']:
            raise permissions.PermissionDenied("Only admin or owner can create a theater.")
        serializer.save(owner=user)

class TheaterRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Theater.objects.all()
    serializer_class = TheaterSerializer
    permission_classes = [IsAdminOrOwner]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Theater.objects.all()
        elif user.role == 'owner':
            return Theater.objects.filter(owner=user)
        return Theater.objects.none()
    
 



class MovieListCreateView(generics.ListCreateAPIView):
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_superuser or user.role == 'user':
            queryset = Movie.objects.all()
        elif user.role == 'owner':
            queryset = Movie.objects.filter(owner=user)
        else:
            return Movie.objects.none()

        theater = self.request.query_params.get("theater")
        if theater:
            queryset = queryset.filter(theater_id=theater)

        return queryset


    def perform_create(self, serializer):
        
        if self.request.user.is_superuser or self.request.user.role == 'owner':
            serializer.save(owner=self.request.user)
        else:
            raise permissions.PermissionDenied("Only admin and owner can create movies.")


class MovieRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwnerCanEdit]



class ShowListCreateView(generics.ListCreateAPIView):
    serializer_class = ShowSerializer
    queryset = Show.objects.all().select_related('movie', 'theater')

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsOwner()]
        return [permissions.IsAuthenticated()] 
    def get_queryset(self):
        queryset = super().get_queryset()
        movie_id = self.request.query_params.get('movie')

        user = self.request.user
       
        if user.role == 'owner': 
            queryset = queryset.filter(owner=user)

        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class ShowRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Show.objects.all().select_related('movie', 'theater')
    serializer_class = ShowSerializer
    permission_classes = [permissions.AllowAny]  
            
class SeatListCreateView(generics.ListCreateAPIView):
    serializer_class = SeatSerializer
    permission_classes = [permissions.IsAuthenticated] 

    def get_queryset(self):
        show_id = self.kwargs['show_id']
        return Seat.objects.filter(show_id=show_id).order_by('row', 'column')


    def perform_create(self, serializer):
        user = self.request.user
        if user.role != 'owner':
            raise permissions.PermissionDenied("Only owners can create seats.")
        serializer.save()
                
        



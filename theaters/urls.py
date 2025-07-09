from django.urls import path
from .views import *

urlpatterns = [
    path('theaters/', TheaterListCreateView.as_view(), name='theater-list-create'),
    path('theaters/<int:pk>/', TheaterRetrieveUpdateView.as_view(), name='theater-detail'),
    path('movies/', MovieListCreateView.as_view(), name='movie-list-create'),
    path('movies/<int:pk>/', MovieRetrieveUpdateDestroyView.as_view(), name='movie-detail'),
    path('shows/', ShowListCreateView.as_view(), name='shows'),
    path('shows/<int:show_id>/seats/', SeatListCreateView.as_view(), name='seat-list-create'),
    path("shows/<int:pk>/", ShowRetrieveUpdateDestroyView.as_view(), name="show-detail"),]

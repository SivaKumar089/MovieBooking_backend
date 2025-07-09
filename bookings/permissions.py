from rest_framework import permissions

# permissions.py

from rest_framework.permissions import BasePermission

class IsBookingOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsTheaterOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'owner'
from rest_framework.permissions import BasePermission

class IsUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'user'

class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'owner'

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'admin'

class IsBookingOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'owner'
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrOwner(BasePermission):
    """
    Allows access only to users with admin or owner roles for unsafe methods.
    Safe methods (GET) are allowed for any authenticated user.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role in ['admin', 'owner']
from rest_framework.permissions import BasePermission

from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'owner']

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        if request.user.role == 'owner':
            return obj.owner == request.user
        return False

from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrOwnerMovie(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in ['admin', 'owner']

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == 'admin' or obj.created_by == request.user

from rest_framework import permissions

class IsAdminOrOwnerCanEdit(permissions.BasePermission):
    """
    Custom permission:
    - Admin can edit/delete all
    - Owner can edit/delete their own movies
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_superuser or obj.owner == request.user

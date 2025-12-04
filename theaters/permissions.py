from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwner(BasePermission):
    def has_permission(self, request, view):
        print("=== IsOwner Permission Checking ===")
        print("Method:", request.method)
        print("User:", request.user)

        # AUTHENTICATION FIX (request.user is now valid)
        print("Is Authenticated:", request.user.is_authenticated)

        if request.method in SAFE_METHODS:
            print("Allowed SAFE method")
            return request.user.is_authenticated
        
        role = getattr(request.user, 'role', None)
        print("User Role:", role)
        print("POST Allowed:", role in ['admin', 'owner'])

        return role in ['admin', 'owner']





class IsAdminOrOwner(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'owner']

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.owner == request.user


class IsAdminOrOwnerCanEdit(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow GET, HEAD, OPTIONS for all authenticated users
        if request.method in SAFE_METHODS:
            return True

        # Only owner can edit
        return obj.owner == request.user

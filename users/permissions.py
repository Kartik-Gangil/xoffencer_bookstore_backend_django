from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated, is staff, and has the 'admin' role
        return bool(request.user and request.user.is_authenticated and request.user.is_staff and request.user.role == 'admin')
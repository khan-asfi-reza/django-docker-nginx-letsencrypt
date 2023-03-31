from rest_framework.permissions import BasePermission


class UserViewPermissionClass(BasePermission):

    def has_permission(self, request, view):
        return request.method == "POST" or (
                request.method in ["GET", "PUT", "PATCH"] and request.user.is_authenticated
        )

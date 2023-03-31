from rest_framework import permissions


class PostPublicPermission(permissions.IsAuthenticatedOrReadOnly):
    message = 'Adding customers not allowed.'

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or request.method == "GET"


class PostStrictPermission(permissions.IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user

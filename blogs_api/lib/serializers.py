from rest_framework import serializers


class RequestUserCreateMixin:
    """
    Mixin to set user as request user
    """
    def create(self, validated_data):
        validated_data[self.Meta.user_key] = self.context.get("request").user
        return super().create(validated_data)

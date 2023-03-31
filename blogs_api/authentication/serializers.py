from rest_framework_simplejwt.views import TokenRefreshView

from account.serializers import UserPublicBaseSerializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer as BaseTokenObtainSerializer,
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken


class TokenObtainPairSerializer(BaseTokenObtainSerializer):
    class Meta:
        read_only_fields = ["user"]
        swagger_example = {"username": "user", "password": "123"}

    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        data["user"] = UserPublicBaseSerializer(instance=self.user).data
        return data

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.ReadOnlyField()
    user = UserPublicBaseSerializer(read_only=True, required=False, write_only=False)

    class Meta:
        read_only_fields = ["user", "access"]

    def validate(self, attrs):
        request = self.context["request"]

        refresh = RefreshToken(attrs["refresh"])
        data = {
            "access": str(refresh.access_token),
            "user": UserPublicBaseSerializer(instance=request.user).data
        }
        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()

            data["refresh"] = str(refresh)

        return data

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

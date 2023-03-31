from django.db.models import Case, F, Exists, OuterRef
from django.shortcuts import get_object_or_404
from drf_yasg.openapi import Parameter, IN_QUERY, Schema
from drf_yasg.utils import swagger_auto_schema, no_body
from rest_framework import viewsets, parsers, status
from rest_framework.decorators import action
from rest_framework.response import Response

from account.models import User, UserDetails, Follower
from account.permissions import UserViewPermissionClass
from account.serializers import (UserSerializer, UserPublicBaseSerializer, ProfilePictureUploadSerializer,
                                 UserDetailsSerializer,
                                 PasswordChangeSerializer, UserDetailsSerializer, UserPublicDetailsSerializer,
                                 FollowerSerializer, FollowerDetailsSerializer)
from rest_framework_extensions.mixins import DetailSerializerMixin, NestedViewSetMixin
from rest_framework.permissions import AllowAny, IsAuthenticated

from lib.response import MessageResponse, MessageResponseSchema
from lib.views import retrieve_api, list_api


class UserViewSet(DetailSerializerMixin,
                  viewsets.GenericViewSet,
                  viewsets.mixins.CreateModelMixin,
                  viewsets.mixins.RetrieveModelMixin,
                  viewsets.mixins.UpdateModelMixin
                  ):
    """
    UserViewSet handles user creation, update, retrieve and delete
    """
    serializer_class = UserSerializer
    serializer_detail_class = UserPublicBaseSerializer
    queryset = User.objects.all()
    permission_classes = [
        UserViewPermissionClass
    ]
    lookup_url_kwarg = "id"

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(methods=['post'], request_body=ProfilePictureUploadSerializer)
    @action(detail=False, parser_classes=(parsers.MultiPartParser,), methods=["post"])
    def upload_profile_picture(self, request, *args, **kwargs):
        """
        Updates / Uploads user profile picture to Cloud Storage
        and link the image url to User profile_picture_url
        """
        user = self.get_object()
        serializer = ProfilePictureUploadSerializer(data=request.FILES, instance=user)
        data = serializer.save()
        return Response(
            data,
            status=status.HTTP_201_CREATED
        )

    @action(methods=["put", "patch"], detail=False)
    def edit(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    @swagger_auto_schema(methods=['get'],
                         manual_parameters=[
                             Parameter('code', IN_QUERY, type='str'),
                         ],
                         responses={
                             200: MessageResponseSchema("Successfully verified")
                         }
                         )
    @action(detail=False, methods=["get"], permission_classes=[AllowAny, ])
    def verify(self, request, *args, **kwargs):
        """
        Updates / Uploads user profile picture to Cloud Storage
        and link the image url to User profile_picture_url
        """
        code = request.GET.get("code", None)
        if not code:
            return Response({"error": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)
        User.verify_email(code)
        return MessageResponse(message="Successfully verified")

    @swagger_auto_schema(methods=['post'],
                         request_body=no_body,
                         responses={
                             201: MessageResponseSchema("Sent verification mail")
                         }
                         )
    @action(detail=False, methods=["post"])
    def send_verification(self, request, *args, **kwargs):
        """
        Sends verification mail
        """
        user = request.user
        user.send_verification_email(request)
        return MessageResponse(message="Sent verification mail", status=status.HTTP_201_CREATED)

    @swagger_auto_schema(methods=['post'],
                         request_body=PasswordChangeSerializer,
                         responses={
                             201: MessageResponseSchema("Password changed")
                         }
                         )
    @action(detail=False, methods=["post"])
    def change_password(self, request, *args, **kwargs):
        """
        Change User password
        """
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return MessageResponse(message="Password changed", status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        responses={
            200: UserPublicDetailsSerializer()
        }
    )
    @action(methods=["get"], detail=True, permission_classes=[AllowAny])
    def details(self, request, *args, **kwargs):
        return retrieve_api(
            get_object_or_404(User.objects.details_queryset(), id=kwargs.get("id")),
            UserPublicDetailsSerializer
        )

    @swagger_auto_schema(
        request_body=FollowerSerializer(),
        responses={
            200: FollowerSerializer()
        }
    )
    @action(methods=["post"], detail=False, permission_classes=[IsAuthenticated])
    def follow(self, request, *args, **kwargs):
        """
        Follow a user
        """
        serializer = FollowerSerializer(context=self.get_serializer_context(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        request_body=FollowerSerializer(),
        responses={
            200: MessageResponseSchema(message="Unfollowed")
        }
    )
    @action(methods=["post"], detail=False, permission_classes=[IsAuthenticated])
    def unfollow(self, request, *args, **kwargs):
        """
        Unfollow a user
        """
        serializer = FollowerSerializer(context=self.get_serializer_context(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.delete()
        return MessageResponse(message="Unfollowed", status=status.HTTP_204_NO_CONTENT)

    @action(methods=["get"], detail=True)
    def followers(self, request, *args, **kwargs):
        """
        List of followers paginated
        """
        return list_api(
            request,
            self,
            queryset=User.objects.filter(
                follow_user_owner__following=kwargs.get("id")
            ).annotate(
                is_following=Exists(Follower.objects.filter(user=OuterRef("id"), following=kwargs.get("id")))
            ),
            serializer=FollowerDetailsSerializer,
            paginator=self.paginator
        )

    @action(methods=["get"], detail=False)
    def followings(self, request, *args, **kwargs):
        """
        List of followers paginated
        """
        return list_api(
            request,
            self,
            queryset=User.objects.filter(
                following_user__user=self.request.user
            ),
            serializer=self.serializer_detail_class,
            paginator=self.paginator
        )


class UserDetailsViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    model = UserDetails
    queryset = UserDetails.objects.all()
    serializer_class = UserDetailsSerializer
    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return self.queryset.filter(
            user_id=self.request.user.id
        )

    def get_object(self):
        return get_object_or_404(self.queryset, user_id=self.request.user.id)

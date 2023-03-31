import json
import mimetypes
import os.path
from uuid import uuid4

from cryptography.fernet import InvalidToken
from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
from django.core.files import File
from django.db.models import Count
from rest_framework.exceptions import ValidationError

from django.db import models
from django.http import HttpRequest

from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

from blogs_api import settings
from blogs_api.config.base import ENCRYPTION
from lib.backends import StorageService
from lib.models import TimeStampedModel
from core.tasks import send_email


class UserManager(BaseUserManager):

    def details_queryset(self):
        return self.get_queryset().annotate(
            follower_count=Count("follow_root_user"),
            following_count=Count("following_user"),
            blog_count=Count("blog")
        )


class User(AbstractUser, TimeStampedModel):
    """
    Abstract base class for an account with Auth0 login
    """
    name = models.CharField(max_length=256, null=False, blank=True)
    profile_picture_url = models.URLField(max_length=1024, null=False, blank=True)
    is_verified = models.BooleanField(default=False)
    phone_number = PhoneNumberField(blank=True, null=False)
    bio = models.CharField(max_length=256, blank=True)
    objects = UserManager()

    def __str__(self):
        return self.name

    def build_profile_picture_url(self, file_name: str) -> str:
        """
        Builds profile picture url from file name and user id
        :param file_name: str | Name of the file uploaded
        :return: str | Full unique filename
        """
        return f"{self.id}-{uuid4()}{os.path.splitext(file_name)[1]}"

    def upload_profile_picture(self, validated_data: dict[str, File]) -> str:
        """
        Uploads profile picture to cloud storage and gets image url
        and stores the image url
        :param validated_data: Contains validated profile_picture data
        :return:
        """
        file = validated_data["profile_picture"]
        file_name = file.name
        url = StorageService.upload_file(
            file,
            file_name=self.build_profile_picture_url(file_name),
            content_type=mimetypes.guess_type(file_name)[0]
        )
        self.profile_picture_url = url
        self.save()
        return url

    def send_verification_email(self, request: HttpRequest):
        """
        Sends verification email to user's email account
        :return: None
        """
        if not self.is_verified:
            key = ENCRYPTION.encrypt(
                json.dumps(
                    {
                        "email": self.email,
                        "id": self.id,
                        "username": self.username
                    }
                ).encode("utf-8")
            ).decode("utf-8")
            message = f"""
                <a href="{request.scheme}://{request.get_host()}/api/v1/user/verify?code={key}">
                    Verify account for Blogs
                </a>
            """
            send_email.delay(
                "Verify account",
                "",
                settings.DEFAULT_FROM_EMAIL,
                [
                    self.email
                ],
                html_message=message,
            )

    @classmethod
    def verify_email(cls, code: str):
        """
        Verifies Email
        :param code: verification code
        :return:
        """
        try:
            data = json.loads(ENCRYPTION.decrypt(code).decode("utf-8"))
            _id = data.pop("id")
            user = cls.objects.get(id=_id)
            for key in data:
                if data[key] != getattr(user, key):
                    raise KeyError
            user.is_verified = True
            user.save()
        except (json.JSONDecodeError, KeyError, InvalidToken):
            raise ValidationError("Invalid Verification Code")


class UserDetails(TimeStampedModel):
    """
    User Details | Stores Additional details about user
    EG: User address, phone number etc
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="user_address"
    )
    address_line_1 = models.TextField(null=False, blank=True)
    address_line_2 = models.TextField(null=False, blank=True)
    country = CountryField(blank=True)
    city = models.CharField(max_length=256, null=False, blank=True)
    state = models.CharField(max_length=256, null=False, blank=True)
    zip_code = models.CharField(max_length=128, null=False, blank=True)

    def __str__(self):
        return self.user_id


class Follower(TimeStampedModel):
    """
    User follower relationship
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follow_user_owner")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following_user")

    def __str__(self):
        return f"{self.user_id} - {self.following_id}"

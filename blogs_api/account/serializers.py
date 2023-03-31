from django.contrib.auth import get_user_model
# rest framework imports
from rest_framework.fields import EmailField, ImageField, CurrentUserDefault, IntegerField, BooleanField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import (
    Serializer,
    ModelSerializer,
    ValidationError,
    CharField,
)

from rest_framework.validators import UniqueValidator
# django phone number field import
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework_extensions.serializers import PartialUpdateSerializerMixin

from account.models import UserDetails, Follower
from lib.serializers import RequestUserCreateMixin

User = get_user_model()


# User Serializer
class UserSerializer(PartialUpdateSerializerMixin, ModelSerializer):
    """
    Serializer that will be used to create a user and
    preview user's personal details
    """
    query_set = User.objects.all()

    username = CharField(trim_whitespace=True,
                         validators=[
                             UniqueValidator(
                                 queryset=query_set,
                                 message="Username is already used"
                             )
                         ]
                         )
    email = EmailField(validators=[
        UniqueValidator(
            queryset=query_set,
            message="Email is already used"
        )
    ],
        default=None,
        required=False,
        allow_null=True,
        allow_blank=True)
    phone_number = PhoneNumberField()
    password = CharField(required=True,
                         style={"input_type": "password"},
                         trim_whitespace=False,
                         write_only=True)

    class Meta:
        # Model User
        model = User
        # Fields
        fields = ["id", "phone_number", "name", "password", "username", "email", "profile_picture_url"]
        # Read only Fields
        read_only_fields = ["id", "profile_picture_url"]
        # Example
        swagger_example = {
            "phone_number": "+41524204242"
        }

    def create(self, validated_data):
        # Create User
        user = User(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserPublicBaseSerializer(ModelSerializer):
    """
    Base Public Serializer, contains basic user details
    """

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "name",
            "profile_picture_url"
        ]
        read_only_fields = [
            "id",
            "username",
            "name",
            "profile_picture_url"
        ]


class UserPublicDetailsSerializer(ModelSerializer):
    """
    Class User profile serializer containing user's details
    """
    follower_count = IntegerField(read_only=True)
    following_count = IntegerField(read_only=True)
    blog_count = IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "name",
            "profile_picture_url",
            "follower_count",
            "following_count",
            "blog_count"
        ]


class PasswordChangeSerializer(Serializer):
    """
    Password changing handler
    Validate old password and set new passport
    """
    old_password = CharField(required=True,
                             style={"input_type": "password"},
                             trim_whitespace=False)
    new_password = CharField(required=True,
                             style={"input_type": "password"},
                             trim_whitespace=False)

    def validate(self, attrs):
        """
        Validate Old password if old password is right or wrong
        """
        request = self.context.get("request")
        old_password = attrs.get("old_password")
        if not request.user.check_password(old_password):
            raise ValidationError({"error": ["Old password is wrong"]})
        return attrs

    def create(self, validated_data):
        # Create new password
        user = self.context.get("request").user
        user.set_password(validated_data.get("new_password"))
        user.save()
        return user

    def update(self, instance, validated_data):
        pass


class ForgotPasswordSerializer(Serializer):
    """
    Forgot password handler
    """
    phone_number = PhoneNumberField(trim_whitespace=True)
    email = EmailField(trim_whitespace=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ProfilePictureUploadSerializer(Serializer):
    """
    Upload profile picture handler
    """
    profile_picture = ImageField(write_only=True)
    profile_picture_url = CharField(read_only=True)

    def create(self, validated_data):
        """
        Get file and upload to S3 Storage and get url
        Store the url in db as profile picture
        """
        return self.instance.upload_profile_picture(validated_data)

    def save(self, **kwargs):
        self.is_valid(raise_exception=True)
        return {
            "profile_picture_url": self.create(self.validated_data)
        }

    def update(self, instance, validated_data):
        ...


class UserDetailsSerializer(PartialUpdateSerializerMixin, ModelSerializer):
    """
    User details containing user's personal details
    """
    user = PrimaryKeyRelatedField(queryset=User.objects.all(), default=CurrentUserDefault(),
                                  validators=[UniqueValidator])

    class Meta:
        model = UserDetails
        fields = "__all__"
        read_only_fields = [
            "id", "user"
        ]

    def create(self, validated_data):
        return self.Meta.model.objects.update_or_create(user=validated_data.pop("user"), defaults=validated_data)


class FollowerSerializer(ModelSerializer):
    """
    Follow Relationship Create Serializer
    """
    user = UserDetailsSerializer(read_only=True)

    class Meta:
        model = Follower
        fields = "__all__"
        read_only_fields = ["user"]
        user_key = "user"

    def create(self, validated_data):
        validated_data[self.Meta.user_key] = self.context.get("request").user
        return self.Meta.model.objects.get_or_create(
            **validated_data
        )[0]

    def delete(self):
        validated_data = self.validated_data
        validated_data[self.Meta.user_key] = self.context.get("request").user
        return self.Meta.model.objects.filter(
            **validated_data
        ).delete()


class FollowerDetailsSerializer(ModelSerializer):
    """
    Details of followers
    """
    is_following = BooleanField()

    class Meta:
        model = User
        fields = ["id", "name", "username", "profile_picture_url", "is_following"]

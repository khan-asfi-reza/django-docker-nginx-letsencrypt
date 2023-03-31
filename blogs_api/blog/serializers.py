from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from blog.models import Tag, Blog, Comment, Vote, UniqueVisitor
from account.serializers import UserPublicBaseSerializer
from lib.serializers import RequestUserCreateMixin


class TagSerializer(serializers.ModelSerializer):
    """
    Tag Creation Serializer
    """
    count = serializers.IntegerField(default=0, read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "tag", "count"]

    def create(self, validated_data):
        return self.Meta.model.objects.get_or_create(**validated_data)[0]


class BlogSerializer(RequestUserCreateMixin, serializers.ModelSerializer):
    """
    Responsible to handle blogs
    """
    author = UserPublicBaseSerializer(read_only=True)
    tags = serializers.SlugRelatedField(slug_field="tag", queryset=Tag.objects.all(), many=True, allow_empty=True)
    up_vote_count = serializers.IntegerField(read_only=True)
    down_vote_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    unique_visitor_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Blog
        fields = "__all__"
        user_key = "author"
        read_only_fields = [
            "id",
            "view_count",
            "is_banned",
            "deleted_at",
        ]


class BlogSearchSerializer(BlogSerializer):
    tags = serializers.ListField(read_only=True)


class CommentSerializer(RequestUserCreateMixin, serializers.ModelSerializer, ):
    """
    Responsible for creating comments and presenting them
    """
    author = UserPublicBaseSerializer(read_only=True)

    class Meta:
        model = Comment
        user_key = "author"
        fields = "__all__"


class VoteSerializer(RequestUserCreateMixin, serializers.ModelSerializer, ):
    """
    Responsible for creating blog vote and presenting them
    """
    author = UserPublicBaseSerializer(read_only=True)

    class Meta:
        model = Vote
        user_key = "author"
        fields = "__all__"


class UniqueVisitorSerializer(RequestUserCreateMixin, serializers.ModelSerializer):
    """
    Responsible for creating blog vote and presenting them
    """
    author = UserPublicBaseSerializer(read_only=True)

    class Meta:
        model = UniqueVisitor
        user_key = "author"
        fields = "__all__"

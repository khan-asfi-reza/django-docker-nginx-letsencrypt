from typing import Any

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from drf_yasg.openapi import Parameter, IN_QUERY
from drf_yasg.utils import swagger_auto_schema
from elasticsearch_dsl import Q as EsQ
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.permissions import AllowAny, IsAuthenticated

from blog.documents import TagDocument, BlogDocument
from blog.models import Blog, Comment, Vote, Tag, UniqueVisitor
from blog.permissions import PostPublicPermission
from blog.search import SearchViewSetMixin, FilterField
from blog.serializers import BlogSerializer, CommentSerializer, VoteSerializer, TagSerializer, UniqueVisitorSerializer, \
    BlogSearchSerializer
from lib.views import list_api, retrieve_api


class TagViewSet(viewsets.GenericViewSet,
                 SearchViewSetMixin,
                 viewsets.mixins.CreateModelMixin,
                 viewsets.mixins.ListModelMixin,
                 viewsets.mixins.RetrieveModelMixin, ):
    """
    Tag API set
    get: Gets Tag
    list: List of tags
    """
    queryset = Tag.objects.get_active_tags()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    document_class = TagDocument
    filter_params = (
        FilterField("tag", is_required=True),
    )

    def generate_q_clause(self):
        return EsQ("match_phrase_prefix", tag=self.filter_kwargs["tag"])

    @swagger_auto_schema(methods=['get'],
                         manual_parameters=[
                             Parameter('tag', IN_QUERY, type='str'),
                         ],
                         )
    @action(methods=["get"], detail=False)
    def search(self, request, *args, **kwargs):
        """
        Search tag via keyword
        """
        return list_api(
            request,
            self,
            queryset=self.es_search(),
            serializer=self.get_serializer,
            paginator=self.paginator
        )


class BlogsViewSet(viewsets.ModelViewSet, SearchViewSetMixin):
    """
    Blog API Set
    get: Returns Blog List
    post: Creates Blog
    put: Update blog
    delete: Set blog for deletion
    """
    queryset = Blog.objects.all_posts_with_details()
    serializer_class = BlogSerializer
    permission_classes = [PostPublicPermission]
    pagination_class = CursorPagination
    document_class = BlogDocument
    filter_params = (
        FilterField("title"),
        FilterField("text"),
    )

    def validate_filter(self, filter_data: dict[str, Any]):
        """
        Must have either text or title in the filter_data
        :param filter_data:
        :return:
        """
        if not filter_data:
            raise ValidationError("Must have title or text")

    def generate_q_clause(self):
        should_clause = []
        title = self.filter_kwargs.get("title", "")
        text = self.filter_kwargs.get("text", "")
        if title:
            should_clause.append(EsQ("match", title=title))
        if text:
            should_clause.append(EsQ("match", text=text))
        return EsQ("bool", should=should_clause)

    def get_object(self):
        queryset = self.queryset
        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
        )
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self) -> QuerySet[Blog]:
        """
        To add: User preference blogs | Blogs based on following authors and subscribed tags
        :return: QuerySet[Blog]
        """
        return Blog.objects.get_posts_with_details()

    def perform_destroy(self, instance: Blog):
        instance.delete_blog()

    @action(methods=["get"], detail=False, permission_classes=[IsAuthenticated])
    def archived_posts(self, request, *args, **kwargs) -> Response:
        """
        Returns archived posts of user
        """
        return list_api(
            request,
            self,
            queryset=Blog.objects.get_archived_posts(author=request.user.id),
            serializer=self.get_serializer,
            paginator=self.paginator
        )

    @action(methods=["get"], detail=False, permission_classes=[IsAuthenticated])
    def deleted_posts(self, request, *args, **kwargs) -> Response:
        """
        Returns archived posts of user
        """
        return list_api(
            request,
            self,
            queryset=Blog.objects.get_deleted_posts(author=request.user.id),
            serializer=self.get_serializer,
            paginator=self.paginator
        )

    @swagger_auto_schema(methods=['get'],
                         manual_parameters=[
                             Parameter('title', IN_QUERY, type='str'),
                             Parameter('text', IN_QUERY, type='str'),
                         ],

                         )
    @action(methods=["get"], detail=False, permission_classes=[AllowAny])
    def search(self, request, *args, **kwargs):
        """
        Search content with keyword
        """
        return list_api(
            request,
            self,
            queryset=self.es_search(),
            serializer=BlogSearchSerializer,
            paginator=self.paginator
        )


class CommentViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    Comment ViewSet
    get: Comment Retrieve Using ID
    get<list>: Comment List
    post: Create Comment
    delete: Comment Delete
    """
    queryset = Comment.objects.all()
    permission_classes = [PostPublicPermission]
    serializer_class = CommentSerializer
    pagination_class = CursorPagination

    def get_queryset(self) -> QuerySet[Comment]:
        """
        To add: Author Flagged Comments to be at first
        :return: QuerySet[Comment]
        """
        return self.queryset.order_by("-created_at")


class VoteViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    Vote ViewSet
    """
    queryset = Vote.objects.all()
    permission_classes = [PostPublicPermission]
    serializer_class = VoteSerializer
    pagination_class = CursorPagination

    def get_queryset(self) -> QuerySet[Vote]:
        """
        To add: Top Followers | Followings of default user to be on top
        :return: QuerySet[Vote]
        """
        return self.queryset.order_by("-created_at")


class UniqueVisitorViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    Unique Visitor ViewSet
    """
    queryset = UniqueVisitor.objects.all()
    permission_classes = [PostPublicPermission]
    serializer_class = UniqueVisitorSerializer
    pagination_class = CursorPagination

    def get_queryset(self) -> QuerySet[Vote]:
        """
        :return: QuerySet[Vote]
        """
        return self.queryset.order_by("-created_at")

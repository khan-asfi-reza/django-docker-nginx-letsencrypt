from django.urls import path
from rest_framework.routers import SimpleRouter
# Account views
from account.views import UserViewSet, UserDetailsViewSet
# Auth views
from authentication.views import TokenObtainPairView, TokenRefreshView
# Blog views
from blog.views import BlogsViewSet, CommentViewSet, VoteViewSet, TagViewSet, UniqueVisitorViewSet
# Library views
from lib.routers import Router
from rest_framework_extensions.routers import ExtendedSimpleRouter

router = Router()

(
    router.register(r'user', UserViewSet, no_lookup=True)
    .register(
        r'personal_details', UserDetailsViewSet, no_lookup=True
    )
)

router.register(r'tags', TagViewSet)

blog_router = router.register(
    r'blogs', BlogsViewSet, basename="blogs"
)

blog_router.register(
    r'comments', CommentViewSet, basename="comments", parents_query_lookups=["blog"]
)

blog_router.register(
    r'votes', VoteViewSet, basename="votes", parents_query_lookups=["blog"]
)

blog_router.register(
    r'unique_visitors', UniqueVisitorViewSet, basename="unique_visitor", parents_query_lookups=["blog"]
)


urlpatterns = router.urls + [
    path("auth/access_token", TokenObtainPairView.as_view()),
    path("auth/refresh_token", TokenRefreshView.as_view()),
]

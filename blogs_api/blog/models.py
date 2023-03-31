from __future__ import absolute_import, annotations
import mimetypes
import os
from uuid import uuid4

from django.core.files import File
from django.db import models
from django.db.models import QuerySet, Count, Q
from django.forms import formset_factory
from django.utils import timezone
from django.utils.text import slugify

from lib.backends import StorageService
from lib.models import TimeStampedModel, LowerCaseCharField


class TagManager(models.Manager):

    def get_active_tags(self):
        """
        Get Active tags with content count
        :return:
        """
        return self.get_queryset().annotate(
            count=Count("tagcontent")
        )


class Tag(TimeStampedModel):
    """
    Each blog can have multiple tags, tags are unique
    Example: A blog about django can have a tag named 'django'
    """
    tag = models.CharField(max_length=32, unique=True)

    objects = TagManager()

    def __str__(self):
        return self.tag


class TagContent(TimeStampedModel):
    """
    Tag and Content Bridge
    """
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    content = models.ForeignKey("blog.Blog", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.tag_id} - {self.content_id}"


class BlogManager(models.Manager):

    def all_posts_with_details(self) -> QuerySet[Blog]:
        """
        Returns queryset with additional details
        :return:
        """
        return self.get_queryset().annotate(
            up_vote_count=Count("vote", filter=Q(vote__state=VoteChoice.UP_VOTE)),
            down_vote_count=Count("vote", filter=Q(vote__state=VoteChoice.DOWN_VOTE)),
            comment_count=Count("comment"),
            unique_visitor_count=Count("uniquevisitor")
        ).select_related(
            "author",
        ).order_by(
            "-created_at",
            "-view_count"
        )

    def get_public_posts(self) -> QuerySet[Blog]:
        """
        Returns queryset of post that is public to every viewer
        Posts that matches the following criteria will be visible to viewers
        1. is_banned = False
        2. is_draft = False
        3. is_deleted = False
        4. is_archived = False
        :return: QuerySet
        """
        return self.filter(
            is_archived=False,
            is_draft=False,
            is_banned=False,
            is_deleted=False,
        )

    def get_deleted_posts_to_delete(self) -> QuerySet[Blog]:
        """
        Returns deleted post that crossed 15 days time mark, and needs to be deleted
        :return: QuerySet[Blog] Deleted Blogs
        """
        return self.filter(
            is_deleted=True,
        )

    def get_posts_with_details(self) -> QuerySet[Blog]:
        """
        Get public post with details like up_vote_count, down_vote_count and comment_count
        :return:
        """
        queryset: QuerySet[Blog] = self.all_posts_with_details().filter(
            is_archived=False,
            is_draft=False,
            is_banned=False,
            is_deleted=False,
        )
        return queryset.annotate(
            up_vote_count=Count("vote", filter=Q(vote__state=VoteChoice.UP_VOTE)),
            down_vote_count=Count("vote", filter=Q(vote__state=VoteChoice.DOWN_VOTE)),
            comment_count=Count("comment"),
        ).select_related(
            "author",
        ).order_by(
            "-created_at",
            "-view_count"
        )

    def get_archived_posts(self, **kwargs) -> QuerySet[Blog]:
        """
        Archived Blogs
        :param kwargs: Filter Parameters
        :return:
        """
        return self.all_posts_with_details().filter(is_archived=True, **kwargs)

    def get_deleted_posts(self, **kwargs) -> QuerySet[Blog]:
        """
        Deleted Blogs
        :param kwargs: Filter Parameters
        :return:
        """
        return self.all_posts_with_details().filter(is_archived=True, **kwargs)


class Blog(TimeStampedModel):
    """
    Blog Model
    Author: User model
    Title: Title of the blog
    Text: Blog Text | Blog Text can be plain text or html containing image link
    Is Archived: Archived post is not public to viewers
    Is Draft: Post is not published but in draft stage
    Is Deleted: Post is deleted, and deleted post is available for 15 days
    Is Banned: Post can be banned by admin for violating terms and conditions
    """
    author = models.ForeignKey("account.User", on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    text = models.TextField()
    tags = models.ManyToManyField(Tag, through=TagContent)
    view_count = models.PositiveIntegerField(default=0)
    # Archived post is only visible to author
    is_archived = models.BooleanField(default=False)
    # Is Draft / not published by author
    is_draft = models.BooleanField(default=True)
    # Post banned by admin for violating terms
    is_banned = models.BooleanField(default=False)
    # If post is deleted it will be in the database for 15 days
    # A worker will delete the deleted post from database that has been deleted and 15 days ago
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = BlogManager()

    def __str__(self):
        return slugify(self.title)

    @property
    def slug(self):
        """
        Convert spaces or repeated dashes to single dashes. Remove characters that aren't alphanumerics,
        underscores, or hyphens. Convert to lowercase.
        Also strip leading and trailing whitespace, dashes, and underscores.
        Slug version of title
        Example: Title: Django Nginx Docker Tutorial
                 Slug: django-nginx-docker-tutorial
        :return:
        """
        return slugify(self.title)

    def get_up_vote_count(self) -> int:
        """
        Number of up votes on this blog
        :return:  int
        """
        return self.vote_set.filter(state=VoteChoice.UP_VOTE).count()

    def get_down_vote_count(self):
        """
        Number of down votes on this blog
        :return: int
        """
        return self.vote_set.filter(state=VoteChoice.DOWN_VOTE).count()

    def get_comment_count(self):
        """
        Number of comments
        :return: int
        """
        return self.comment_set.count()

    def increase_view(self) -> int:
        """
        Increase view count by one
        :return: int
        """
        self.view_count += 1
        self.save()
        return self.view_count

    def archive_blog(self):
        """
        Archive particular blog
        Set is_archive to True
        :return:
        """
        self.is_archived = True
        self.save()

    def publish_blog(self):
        """
        Publish a blog to public
        Set is_draft = False and is_archive = False and is_delete = False
        :return:
        """
        self.is_archived = False
        self.is_draft = False
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def delete_blog(self):
        """
        Delete blog and set for delete after 15 days
        :return:
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def prepare_author(self) -> dict[str, int | str]:
        """
        Prepare author details for elasticsearch document
        :return: dict[str, int|str] Dictionary object of author details
        """
        return {
            "id": self.author_id,
            "username": self.author.username,
            "email": self.author.email,
            "profile_picture_url": self.author.profile_picture_url,
        }

    def prepare_tags(self) -> list[str]:
        """
        Prepare tags list for elasticsearch document
        :return: list[str] List of tags
        """
        return list(self.tags.values_list("tag", flat=True))


class BlogImage(TimeStampedModel):
    """
    Blog attached images
    """
    blog = models.ForeignKey("blog.Blog", on_delete=models.CASCADE)
    image_url = models.URLField()
    image_alt = models.CharField(max_length=128, blank=True, default="")

    def __str__(self):
        return str(self.blog_id)

    def build_image_url(self, file_name: str) -> str:
        """
        Builds Image URL from file name for blog image
        :param file_name: str | Name of the file uploaded
        :return: str | Full unique filename
        """
        return f"{self.blog_id}-{uuid4()}{os.path.splitext(file_name)[1]}"

    def upload_image(self, validated_data: dict[str, File]):
        """
        Uploads image to cloud storage and retains url and stores in db
        :param validated_data:
        :return:
        """
        file = validated_data["profile_picture"]
        file_name = file.name
        url = StorageService.upload_file(
            file,
            file_name=self.build_image_url(file_name),
            content_type=mimetypes.guess_type(file_name)[0]
        )
        self.profile_picture_url = url
        self.save()
        return url


class VoteChoice(models.TextChoices):
    UP_VOTE = "UP_VOTE"
    DOWN_VOTE = "DOWN_VOTE"


class Vote(TimeStampedModel):
    """
    Vote status
    Blog post up/down voted by author
    """
    author = models.ForeignKey("account.User", on_delete=models.CASCADE)
    blog = models.ForeignKey("blog.Blog", on_delete=models.CASCADE)
    state = models.CharField(choices=VoteChoice.choices, max_length=32)

    def __str__(self):
        return f"{self.author_id} - {self.blog_id} - {self.state}"

    class Meta:
        unique_together = [
            "author", "blog"
        ]


class UniqueVisitor(TimeStampedModel):
    """
    Unique visitor of a blog
    """
    author = models.ForeignKey("account.User", on_delete=models.CASCADE)
    blog = models.ForeignKey("blog.Blog", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.author_id} - {self.blog_id}"

    class Meta:
        unique_together = [
            "author", "blog"
        ]


class Comment(TimeStampedModel):
    """
    Comment on blogs
    """
    author = models.ForeignKey("account.User", on_delete=models.CASCADE)
    blog = models.ForeignKey("blog.Blog", on_delete=models.CASCADE)
    text = models.TextField(max_length=1024)

    def __str__(self):
        return f"{self.author_id} - {self.blog_id} - {self.blog_id[:100]}"

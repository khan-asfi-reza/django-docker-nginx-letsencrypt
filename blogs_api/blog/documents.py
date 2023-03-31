from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from blog.models import Blog, Vote, Comment, Tag, TagContent


@registry.register_document
class TagDocument(Document):
    count = fields.IntegerField()

    class Index:
        name = "tags"
        settings = {
            "number_of_shards": 3,
            "number_of_replicas": 3
        }

    class Django:
        model = Tag
        fields = [
            "tag",
            "id",
            "created_at"
        ]
        related_models = [
            TagContent
        ]

    @staticmethod
    def prepare_count(obj: Tag):
        return obj.tagcontent_set.count()


@registry.register_document
class BlogDocument(Document):
    author = fields.NestedField(
        properties=dict(
            id=fields.IntegerField(),
            name=fields.TextField(),
            username=fields.TextField(),
            profile_picture_url=fields.TextField()
        )
    )

    tags = fields.ListField(fields.KeywordField())
    up_vote_count = fields.LongField()
    down_vote_count = fields.LongField()
    comment_count = fields.LongField()

    class Index:
        name = "blogs"
        settings = {
            "number_of_shards": 3,
            "number_of_replicas": 3
        }

    class Django:
        model = Blog
        fields = [
            "id",
            "title",
            "text",
            "view_count",
            "is_archived",
            "is_draft",
            "is_banned",
            "is_deleted",
            "created_at",

        ]

        related_models = [
            Vote,
            Comment
        ]

    @staticmethod
    def prepare_author(obj: Blog):
        return obj.prepare_author()

    @staticmethod
    def prepare_up_vote_count(obj: Blog):
        return obj.get_up_vote_count()

    @staticmethod
    def prepare_down_vote_count(obj: Blog):
        return obj.get_down_vote_count()

    @staticmethod
    def prepare_comment_count(obj: Blog):
        return obj.get_comment_count()

    @staticmethod
    def prepare_tags(obj: Blog):
        return obj.prepare_tags()

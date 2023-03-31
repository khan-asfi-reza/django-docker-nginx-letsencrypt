from dataclasses import dataclass
from typing import Any, Type

from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.search import Search
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request


@dataclass
class FilterField:
    """
    Filter Field for get query
    field_name: str
    is_required: bool
    """
    field_name: str
    is_required: bool = False


class SearchViewSetMixin:
    """
    Elasticsearch mixin
    """
    filter_params: list[FilterField] = list()
    kwargs: dict
    document_class: Type[Document]
    request: Request

    def validate_filter(self, filter_data: dict[str, Any]):
        pass

    def get_filter_kwargs(self) -> dict[str, Any]:
        """
        Returns filter details
        :return: Dict
        """
        ret = {}
        for field in self.filter_params:
            if field.field_name in self.request.GET:
                ret[field.field_name] = self.request.GET[field.field_name]
            elif field.is_required:
                raise ValidationError(f"'{field.field_name}' missing in query")
        self.validate_filter(ret)
        return ret

    @property
    def filter_kwargs(self):
        return self.get_filter_kwargs()

    def generate_q_clause(self):
        return

    def es_search(self):
        max_count = self.filter_kwargs.pop("max_count", 1000)
        search: Search = self.document_class.search().extra(size=max_count).query(
            self.generate_q_clause()
        )
        return search.execute()

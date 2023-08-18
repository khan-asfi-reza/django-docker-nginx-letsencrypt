from typing import Type, Any

from django.contrib.auth import logout
from django.db.models import QuerySet
from django.shortcuts import redirect
from rest_framework.response import Response
from rest_framework.serializers import Serializer


def logout_view(request):
    logout(request)
    return redirect("admin:login")


def list_api(request, view, queryset: QuerySet, serializer: Any, paginator=None, ) -> Response:
    """
    Functional way of ViewSet `list` method
    :param request: HTTP Request | Rest Framework Request Class Object
    :param view: ViewSet
    :param queryset: QuerySet
    :param serializer: Serializer class
    :param paginator: Paginator Class
    :return: Response
    """
    if paginator:
        page = paginator.paginate_queryset(queryset, request, view=view)
        if page is not None:
            serializer = serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
    serializer = serializer(queryset, many=True)
    return Response(serializer.data)


def retrieve_api(instance: Any, serializer: Any):
    """
    Functional way of ViewSet `retrieve` method
    :param instance:
    :param serializer:
    :return:
    """
    serializer = serializer(instance)
    return Response(serializer.data)

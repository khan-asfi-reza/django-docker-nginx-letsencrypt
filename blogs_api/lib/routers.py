from copy import deepcopy

from django.urls import re_path
from rest_framework.routers import SimpleRouter, Route, DynamicRoute
from rest_framework_extensions.routers import NestedRegistryItem as ExtensionNestedRegistryItem

from blogs_api import settings


def compose_parent_pk_kwarg_name(value):
    return '{0}{1}'.format(
        settings.DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX,
        value
    )


class NestedRegistryItem(ExtensionNestedRegistryItem):

    def register(self, prefix, viewset, basename=None, no_lookup=False, parents_query_lookups=None, ):
        if parents_query_lookups is None:
            parents_query_lookups = []
        self.router.pre_register(
            prefix=self.get_prefix(
                current_prefix=prefix,
                parents_query_lookups=parents_query_lookups),
            viewset=viewset,
            basename=basename,
            no_lookup=no_lookup,
        )
        return NestedRegistryItem(
            router=self.router,
            parent_prefix=prefix,
            parent_item=self,
            parent_viewset=viewset
        )

    def get_prefix(self, current_prefix, parents_query_lookups):
        return '{0}/{1}'.format(
            self.get_parent_prefix(parents_query_lookups),
            current_prefix
        )

    def get_parent_prefix(self, parents_query_lookups):
        prefix = '/'
        current_item = self
        i = len(parents_query_lookups) - 1
        while current_item:
            parent_lookup_value_regex = getattr(
                current_item.parent_viewset, 'lookup_value_regex', '[^/.]+')
            prefix = '{parent_prefix}/{look_up_value}{prefix}'.format(
                parent_prefix=current_item.parent_prefix,
                look_up_value='(?P<{parent_pk_kwarg_name}>{parent_lookup_value_regex})/'.format(
                    parent_pk_kwarg_name=compose_parent_pk_kwarg_name(
                        parents_query_lookups[i]) if parents_query_lookups else '',
                    parent_lookup_value_regex=parent_lookup_value_regex,
                ) if parents_query_lookups else '',
                prefix=prefix
            )

            i -= 1
            current_item = current_item.parent_item
        return prefix.strip('/')


class NestedRouterMixin(SimpleRouter):
    def pre_register(self, prefix, viewset, basename=None, no_lookup=False):
        if basename is None:
            basename = self.get_default_basename(viewset)
        self.registry.append((prefix, viewset, basename, no_lookup))

        # invalidate the urls cache
        if hasattr(self, '_urls'):
            del self._urls

    def register(self, *args, **kwargs):
        self.pre_register(*args, **kwargs)
        return NestedRegistryItem(
            router=self,
            parent_prefix=self.registry[-1][0],
            parent_viewset=self.registry[-1][1]
        )


class Router(NestedRouterMixin):
    routes = [

        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        # Dynamically generated list routes. Generated using
        # @action(detail=False) decorator on methods of the viewset.
        DynamicRoute(
            url=r'^{prefix}/{url_path}{trailing_slash}$',
            name='{basename}-{url_name}',
            detail=False,
            initkwargs={}
        ),
        # Detail route.
        Route(
            url=r'^{prefix}/{lookup}$',
            mapping={
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Instance'}
        ),
        # Dynamically generated detail routes. Generated using
        # @action(detail=True) decorator on methods of the viewset.
        DynamicRoute(
            url=r'^{prefix}/{lookup}{url_path}{trailing_slash}$',
            name='{basename}-{url_name}',
            detail=True,
            initkwargs={}
        ),
    ]

    def register(self, prefix, viewset, basename=None, no_lookup=False):
        if basename is None:
            basename = self.get_default_basename(viewset)
        self.registry.append((prefix, viewset, basename, no_lookup))

        # invalidate the urls cache
        if hasattr(self, '_urls'):
            del self._urls

        return NestedRegistryItem(
            router=self,
            parent_prefix=self.registry[-1][0],
            parent_viewset=self.registry[-1][1]
        )

    def get_lookup_regex(self, viewset, lookup_prefix=''):
        """
        Given a viewset, return the portion of URL regex that is used
        to match against a single instance.

        Note that lookup_prefix is not used directly inside REST rest_framework
        itself, but is required in order to nicely support nested router
        implementations, such as drf-nested-routers.

        https://github.com/alanjds/drf-nested-routers
        """
        base_regex = '(?P<{lookup_prefix}{lookup_url_kwarg}>{lookup_value}){trailing_slash}'
        # Use `pk` as default field, unset set.  Default regex should not
        # consume `.json` style suffixes and should break at '/' boundaries.
        lookup_field = getattr(viewset, 'lookup_field', 'pk')
        lookup_url_kwarg = getattr(viewset, 'lookup_url_kwarg', None) or lookup_field
        lookup_value = getattr(viewset, 'lookup_value_regex', '[^/.]+')
        return base_regex.format(
            lookup_prefix=lookup_prefix,
            lookup_url_kwarg=lookup_url_kwarg,
            lookup_value=lookup_value,
            trailing_slash=self.trailing_slash
        )

    def get_urls(self):
        """
        Use the registered viewsets to generate a list of URL patterns.
        """
        ret = []

        for prefix, viewset, basename, no_lookup in self.registry:
            lookup = self.get_lookup_regex(viewset)
            routes = deepcopy(self.get_routes(viewset))

            for _route in routes:
                route = deepcopy(_route)
                if no_lookup:
                    if route.name == '{basename}-list':
                        route.mapping.update(
                            {
                                'put': 'update',
                                'patch': 'partial_update',
                                'delete': 'destroy'
                            }
                        )
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue
                if no_lookup and "get" in mapping and mapping["get"] == "list":
                    continue
                # Build the url pattern
                regex = route.url.format(
                    prefix=prefix,
                    lookup='' if no_lookup and route.name == '{basename}-detail' else lookup,
                    trailing_slash=self.trailing_slash
                )

                # If there is no prefix, the first part of the url is probably
                #   controlled by project's urls.py and the router is in an app,
                #   so a slash in the beginning will (A) cause Django to give
                #   warnings and (B) generate URLS that will require using '//'.
                if not prefix and regex[:2] == '^/':
                    regex = '^' + regex[2:]

                initkwargs = route.initkwargs.copy()
                initkwargs.update({
                    'basename': basename,
                    'detail': route.detail,
                })

                view = viewset.as_view(mapping, **initkwargs)
                name = route.name.format(basename=basename)
                ret.append(re_path(regex, view, name=name))

        return ret

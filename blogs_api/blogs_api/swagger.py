from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)


class ZelfGeneratorClass(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        try:
            for definition in schema.definitions.keys():
                if hasattr(
                        schema.definitions[definition]._NP_serializer,
                        "swagger_example",
                ):
                    examples = schema.definitions[
                        definition
                    ]._NP_serializer.swagger_example
                    for example in examples.keys():
                        if example in schema.definitions[definition]["properties"]:
                            schema.definitions[definition]["properties"][example][
                                "example"
                            ] = examples[example]
        except AttributeError:
            pass
        return schema


SchemaView = get_schema_view(
    openapi.Info(
        title="Blogs API",
        default_version="v1",
        description="Blogs API Endpoint Documentation",
        license=openapi.License(name="EULA"),
    ),
    generator_class=ZelfGeneratorClass,
    public=True,
    # permission_classes=[
    #     permissions.IsAdminUser,
    # ],
    # authentication_classes=[BasicAuthentication, SessionAuthentication],
)

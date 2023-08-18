from drf_yasg import openapi
from rest_framework.response import Response


class MessageResponse(Response):

    def __init__(self, message="", status=None,
                 template_name=None, headers=None,
                 exception=False, content_type=None):
        """
        Alters the init arguments slightly.
        For example, drop 'data', and instead use 'message'.

        Sends a message and status text instead of data
        :example:
        ```
        return MessageResponse(message="", status_text="")
        ```
        """

        super().__init__(
            data={
                "message": message,
                "status": "SUCCESS" if str(status).startswith("2") and not status == 204 else "DELETED" if status == 204
                else "REDIRECT" if str(status).startswith("1") or str(status).startswith("3") else "FAILURE"
            }, status=status,
            template_name=template_name, headers=headers,
            exception=exception, content_type=content_type
        )


class MessageResponseSchema:

    def __new__(cls,  message="", status="SUCCESS"):
        return openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, default=message),
                'status': openapi.Schema(type=openapi.TYPE_STRING, default=status)
            }
        )



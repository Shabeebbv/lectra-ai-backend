from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):

    response = exception_handler(exc, context)

    if response is None:

        return Response(
            {
                "success": False,
                "message": "Something went wrong",
                "errors": []
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    message = response.data.get(
        "detail",
        "Validation error"
    )

    return Response(
        {
            "success": False,
            "message": message,
            "errors": response.data
        },
        status=response.status_code
    )
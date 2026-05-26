import traceback

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):

    response = exception_handler(exc, context)

    if response is None:

        print("EXCEPTION:", str(exc))
        traceback.print_exc()

        return Response(
            {
                "success": False,
                "message": "Something went wrong",
                "errors": []
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # HANDLE DICT ERRORS
    if isinstance(response.data, dict):

        if "detail" in response.data:
            message = response.data["detail"]

        else:
            first_key = next(iter(response.data))
            first_error = response.data[first_key]

            if isinstance(first_error, list):
                message = first_error[0]
            else:
                message = first_error

    # HANDLE LIST ERRORS
    elif isinstance(response.data, list):

        message = response.data[0]

    else:
        message = "Validation error"

    return Response(
        {
            "success": False,
            "message": str(message),
            "errors": response.data
        },
        status=response.status_code
    )
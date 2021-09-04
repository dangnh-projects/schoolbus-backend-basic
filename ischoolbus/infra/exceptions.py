from rest_framework.views import exception_handler


def rest_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data['status'] = response.status_code
        response.data['message'] = response.data['detail']
        del response.data['detail']

    return response

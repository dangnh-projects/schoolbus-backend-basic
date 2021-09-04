from rest_framework import status
from rest_framework.response import Response


class CommonResponse:
    @staticmethod
    def of(data):
        result = {"status": status.HTTP_200_OK, "data": data}
        return Response(result, status=status.HTTP_200_OK)

    @staticmethod
    def of_errors(errors):
        result = {"status": status.HTTP_400_BAD_REQUEST, "data": errors}
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

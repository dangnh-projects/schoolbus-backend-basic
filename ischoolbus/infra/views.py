from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, APIException

from functools import reduce

from django.conf import settings
from django.utils.translation import gettext as _
from django.db.models import Q

from .api_response import CommonResponse


class ProtectedView(APIView):
    permission_classes = (IsAuthenticated,)


class CrudView(ProtectedView):
    def _get_model(self):
        if hasattr(self, "Model"):
            return self.Model
        raise APIException(detail="Child view does not provide model")

    def _get_serializer(self):
        if hasattr(self, "Serializer"):
            return self.Serializer
        raise APIException(detail="Child view does not provide serializer")

    def _get_name(self):
        if hasattr(self, "name"):
            return self.name
        return 'Item'

    def _get_search_fields(self):
        if hasattr(self, "search_fields"):
            return self.search_fields
        return []

    def _construct_search_query(self, search):
        search_fields = self._get_search_fields()

        query = reduce(lambda x, y: x | y,
                       [Q(**{field: search}) for field in search_fields])

        return query

    def get(self, request):
        page = int(request.GET.get('page', 0))
        search = request.GET.get('search', None)
        records_per_page = int(
            request.GET.get('records_per_page', settings.MAX_RECORDS_PER_PAGE))
        low = page * records_per_page
        high = (page + 1) * records_per_page

        if search:
            query = self._construct_search_query(search)
            items = self._get_model().objects.filter(query)[low:high]
            count = self._get_model().objects.filter(query).count()
        else:
            items = self._get_model().objects.all()[low:high]
            count = self._get_model().objects.all().count()

        serializer = self._get_serializer()(items, many=True)
        return CommonResponse.of({"results": serializer.data, "count": count})

    def post(self, request):
        body_data = request.POST
        student_data = body_data.dict()
        serializer = self._get_serializer()(data=student_data)
        if serializer.is_valid():
            serializer.save()
            return CommonResponse.of(serializer.data)
        return CommonResponse.of_errors(serializer.errors)

    def put(self, request, *args, **kwargs):
        body_data = request.POST
        pk = kwargs["pk"]
        item = self._get_model().objects.filter(id=pk).first()

        if not item:
            raise NotFound(detail=_(self._get_name() + ' not exists'))

        item.__dict__.update(**body_data.dict())
        item.save()

        return CommonResponse.of({
            "message": self._get_name() + " updated successfully",
            "data": self._get_serializer()(item).data
        })

    def delete(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        item = self._get_model().objects.filter(id=pk).first()
        if not item:
            raise NotFound()

        item.delete()
        return CommonResponse.of(
            {"message": self._get_name() + " removed successfully"})

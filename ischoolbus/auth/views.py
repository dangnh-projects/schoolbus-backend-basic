from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed, NotFound

from django.contrib.auth import authenticate
from django.utils.translation import gettext as _

from infra.api_response import CommonResponse
from infra.views import ProtectedView
from auth.services import change_password, query_profile, init_data_for_device, init_data_for_login, init_data_for_parent


class LoginView(APIView):
    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        device_id = request.POST.get('device_id', None)
        device_token = request.POST.get('device_token', None)
        device_type = request.POST.get('device_type', None)
        locale = request.POST.get('locale', "en-US")

        user = authenticate(username=username, password=password)

        if user is not None:
            data = init_data_for_login(user)
            if user.is_staff == False:
                data['bus_routes'] = init_data_for_parent(user, locale)

            if device_type != 'web':
                init_data_for_device(user, device_token, device_id,
                                     device_type)

            return CommonResponse.of(data)

        raise AuthenticationFailed(detail=_('Invalid username and password combination. Please try again.'))


class UserProfileView(ProtectedView):
    def get(self, request):
        content = query_profile(request.user)
        return CommonResponse.of(content)


class PingView(ProtectedView):
    def get(self, request):
        content = {'message': 'Pong !'}
        return CommonResponse.of(content)


class ChangePasswordView(ProtectedView):
    def post(self, request):
        new_password = request.POST["new_password"]
        if not new_password:
            raise NotFound(detail="Parameter not found")
        change_password(request.user, new_password)
        return CommonResponse.of({'message': 'Success'})

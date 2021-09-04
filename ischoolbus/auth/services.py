from rest_framework_simplejwt.tokens import RefreshToken
from fcm_django.models import FCMDevice
from core.models import Parent, BusSupervisor
from core.services import query_students_and_routes_for_parent, save_parent_locale


def query_profile(user):
    content = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'groups': [group.name for group in user.groups.all()]
    }

    if user.is_staff:
        supervisor = BusSupervisor.objects.filter(info=user).first()
        if supervisor:
            content['phone_number'] = supervisor.phone_number
            content['avatar'] = supervisor.avatar.url
    else:
        parent = Parent.objects.filter(info=user).first()
        if parent:
            content['phone_number'] = parent.phone_number
            content['avatar'] = parent.avatar.url

    return content


def change_password(user, new_password):
    user.set_password(new_password)
    user.save()


def init_data_for_login(user):
    refresh = RefreshToken.for_user(user)
    data = {
        'token': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
        'user': {
            'username': user.username,
            'email': user.email,
            'supervisor': True if user.is_staff else False
        },
    }

    return data


def init_data_for_parent(user, locale):
    parent = Parent.objects.filter(info=user).first()
    if parent:
        save_parent_locale(parent, locale)
        return query_students_and_routes_for_parent(parent)

    return None


def init_data_for_device(user, device_token, device_id, device_type):
    FCMDevice.objects.get_or_create(user=user,
                                    registration_id=device_token,
                                    device_id=device_id,
                                    type=device_type)

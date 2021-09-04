from django.urls import path
from .views import PingView, UserProfileView, LoginView, ChangePasswordView
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('api/login', LoginView.as_view(), name='LoginView'),
    path('api/token/refresh', jwt_views.TokenRefreshView.as_view(),
         name='TokenRefreshView'),

    path('api/user/', UserProfileView.as_view(), name='UserProfileView'),
    path('api/ping/', PingView.as_view(), name='PingView'),
    path('api/change-password', ChangePasswordView.as_view(),
         name='ChangePasswordView')
]

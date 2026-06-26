from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    VerifyOTPView,
    LoginView,
    VerifyLoginOTPView,
    MeView,
    LogoutView,
    ResendOTPView,
)

urlpatterns = [
    path('register/',          RegisterView.as_view()),
    path('verify-otp/',        VerifyOTPView.as_view()),
    path('login/',             LoginView.as_view()),
    path('verify-login-otp/',  VerifyLoginOTPView.as_view()),  
    path('me/',                MeView.as_view()),
    path('logout/',            LogoutView.as_view()),
    path('resend-otp/',        ResendOTPView.as_view()),
    path('token/refresh/',     TokenRefreshView.as_view()),

]
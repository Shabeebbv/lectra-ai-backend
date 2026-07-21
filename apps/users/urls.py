from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    SaveFCMTokenView,
    VerifyOTPView,
    LoginView,
    VerifyLoginOTPView,
    MeView,
    LogoutView,
    ResendOTPView,
    CustomTokenRefreshView,
    VerifyMFALoginView,
    MFASetupView,
    MFAVerifySetupView,
    MFADisableView,
    MFAStatusView,
)

urlpatterns = [
    path('register/',          RegisterView.as_view()),
    path('verify-otp/',        VerifyOTPView.as_view()),
    path('login/',             LoginView.as_view()),
    path('verify-login-otp/',  VerifyLoginOTPView.as_view()),  
    path('me/',                MeView.as_view()),
    path('logout/',            LogoutView.as_view()),
    path('resend-otp/',        ResendOTPView.as_view()),
    path('token/refresh/',     CustomTokenRefreshView.as_view()),
    path("fcm-token/",SaveFCMTokenView.as_view()),
    path('verify-mfa-otp/', VerifyMFALoginView.as_view()),
    path('mfa/setup/', MFASetupView.as_view()),
    path('mfa/verify-setup/', MFAVerifySetupView.as_view()),
    path('mfa/disable/', MFADisableView.as_view()),
    path('mfa/status/', MFAStatusView.as_view()),
    
]
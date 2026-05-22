from django.urls import path
from .views import RegisterView,VerifyOTPView,LoginView,MeView,ForgotPasswordView,ResetPasswordView,LogoutView,ResendOTPView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view()),
    path('login/', LoginView.as_view()),
    path('me/', MeView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()) ,
    path('token/refresh/', TokenRefreshView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('resend-otp/', ResendOTPView.as_view()),
]
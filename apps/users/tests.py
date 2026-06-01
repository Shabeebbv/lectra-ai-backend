from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.users.models import OTP
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class RegisterTest(APITestCase):

    def test_user_registration(self):

        payload = {
            "full_name": "Shabeeb",
            "phone_number": "+919999999999",
            "password": "test1234"
        }

        response = self.client.post(
            "/api/users/register/",
            payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            User.objects.filter(
                phone_number="+919999999999"
            ).exists()
        )
        
class LoginTest(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            full_name="Test User",
            phone_number="+918888888888",
            password="test1234",
            is_verified=True
        )

    def test_login(self):

        payload = {
            "phone_number": "+918888888888",
            "password": "test1234"
        }

        response = self.client.post(
            "/api/users/login/",
            payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        
        
class VerifyOTPTest(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            full_name="Test User",
            phone_number="+917777777777",
            password="test1234"
        )

        OTP.objects.create(
            user=self.user,
            otp_code="123456",
            purpose=OTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5)
        )

    def test_verify_otp(self):

        payload = {
            "phone_number": "+917777777777",
            "otp": "123456"
        }

        response = self.client.post(
            "/api/users/verify-otp/",
            payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        
        
        

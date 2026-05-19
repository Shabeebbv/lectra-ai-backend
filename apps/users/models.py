from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import random
import string
from django.utils import timezone

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(email, password, **extra_fields)



class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    
    username = None

    email = models.EmailField(unique=True)
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    is_verified = models.BooleanField(default=False)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    

class OTP(models.Model):

    PURPOSE_CHOICES = (
        ('register', 'Register'),
        ('forgot_password', 'Forgot Password'),
    )

    user           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp_code       = models.CharField(max_length=4)
    otp_type       = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    is_used        = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True)
    expires_at     = models.DateTimeField()
    resend_count   = models.IntegerField(default=0)
    last_resent_at = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        ordering = ['-created_at']
 
    def is_expired(self):
        return timezone.now() > self.expires_at
 
    def is_valid(self):
        return not self.is_used and not self.is_expired()
 
    @staticmethod
    def generate_otp():
        return ''.join(random.choices(string.digits, k=4))
 
    def __str__(self):
        return f"{self.user.email} | {self.otp_type} | {self.otp_code}"
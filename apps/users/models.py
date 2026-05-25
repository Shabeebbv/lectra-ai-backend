from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):

    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(phone_number, password, **extra_fields)



class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    
    username = None

    email = models.EmailField(unique=True)
    
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    is_verified = models.BooleanField(default=False)


    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()
    
    def __str__(self):
        return self.phone_number
    
    

class OTP(models.Model):

    class Purpose(models.TextChoices):
        REGISTER = "register", "Register"
        FORGOT_PASSWORD = "forgot_password", "Forgot Password"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='otps'
    )

    otp_code = models.CharField(max_length=6)

    purpose = models.CharField(
        max_length=30,
        choices=Purpose.choices
    )

    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField()

    resend_count = models.IntegerField(default=0)

    last_resent_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'purpose']),
        ]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired()

    def __str__(self):
        return f"{self.user.email} | {self.purpose}"
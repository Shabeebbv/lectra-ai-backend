from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):

    def create_user(
        self,
        full_name,
        email=None,
        phone_number=None,
        password=None,
        **extra_fields
    ):
        if not email and not phone_number:
            raise ValueError("Either email or phone number is required.")

        if email:
            email = self.normalize_email(email)

        user = self.model(
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            **extra_fields
        )

        user.set_unusable_password()
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        full_name,
        email,
        password=None,
        **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(
            full_name=full_name,
            email=email,
            password=password,
            **extra_fields
        )


class User(AbstractUser):

    ROLE_CHOICES = (
        ("super_admin", "Super Admin"),
        ("admin", "Admin"),
        ("user", "User"),
    )

    username = None

    full_name = models.CharField(max_length=150)

    # unique=True removed — enforced instead via partial constraints below,
    # so a soft-deleted user's email/phone can be reused on re-registration.
    email = models.EmailField(null=True, blank=True)

    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        db_index=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="user"
    )

    is_verified = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    blocked_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(is_deleted=False),
                name="unique_active_email",
            ),
            models.UniqueConstraint(
                fields=["phone_number"],
                condition=models.Q(is_deleted=False),
                name="unique_active_phone_number",
            ),
        ]

    def __str__(self):
        return self.full_name or self.email or self.phone_number


class OTP(models.Model):

    class Purpose(models.TextChoices):
        REGISTER = "register", "Register"
        LOGIN = "login", "Login"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    resend_count = models.IntegerField(default=0)
    last_resent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'purpose'])]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired()

    def __str__(self):
        return f"{self.user.phone_number} | {self.purpose}"


class FCMToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fcm_tokens")
    token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.id}"
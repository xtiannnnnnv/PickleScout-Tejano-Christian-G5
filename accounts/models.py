from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model for PickleScout with role-based access.
    Roles: Player (regular user), Court Admin, and System Admin.
    """

    class Role(models.TextChoices):
        PLAYER = 'PLAYER', 'Player'
        COURT_ADMIN = 'COURT_ADMIN', 'Court Administrator'
        SYSTEM_ADMIN = 'SYSTEM_ADMIN', 'System Administrator'

    role = models.CharField(
        max_length=15,
        choices=Role.choices,
        default=Role.PLAYER,
    )
    contact_number = models.CharField(max_length=20, blank=True)
    dupr_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        blank=True,
        null=True,
        help_text='Your DUPR rating (e.g. 3.5)',
    )
    city = models.CharField(max_length=100, blank=True, help_text='Your city or area')
    social_links = models.JSONField(default=list, blank=True)
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

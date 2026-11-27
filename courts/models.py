from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Court(models.Model):
    """A pickleball court listing."""

    class FacilityType(models.TextChoices):
        INDOOR = 'INDOOR', 'Indoor'
        OUTDOOR = 'OUTDOOR', 'Outdoor'
        BOTH = 'BOTH', 'Indoor & Outdoor'

    class SurfaceType(models.TextChoices):
        CONCRETE = 'CONCRETE', 'Concrete'
        ASPHALT = 'ASPHALT', 'Asphalt'
        WOOD = 'WOOD', 'Wood / Hardwood'
        SYNTHETIC = 'SYNTHETIC', 'Synthetic / Sport Court'
        ACRYLIC = 'ACRYLIC', 'Acrylic'
        OTHER = 'OTHER', 'Other'

    # Basic info
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    facility_type = models.CharField(
        max_length=10,
        choices=FacilityType.choices,
        default=FacilityType.OUTDOOR,
    )
    surface_type = models.CharField(
        max_length=15,
        choices=SurfaceType.choices,
        blank=True,
    )
    number_of_courts = models.PositiveIntegerField(default=1)

    # Location
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    province_state = models.CharField(max_length=100, blank=True, verbose_name='Province / State')
    zip_code = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    # Contact & links
    contact_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Operating details
    operating_hours = models.CharField(
        max_length=200, blank=True,
        help_text='e.g. Mon–Fri 6 AM – 10 PM, Sat–Sun 7 AM – 9 PM',
    )
    rental_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        help_text='Price per hour in local currency',
    )

    # Amenities (booleans)
    has_lighting = models.BooleanField(default=False, verbose_name='Lighting')
    has_parking = models.BooleanField(default=False, verbose_name='Parking')
    has_restrooms = models.BooleanField(default=False, verbose_name='Restrooms')
    has_equipment_rental = models.BooleanField(default=False, verbose_name='Equipment Rental')
    has_water_fountain = models.BooleanField(default=False, verbose_name='Water Fountain')
    has_seating = models.BooleanField(default=False, verbose_name='Spectator Seating')
    is_wheelchair_accessible = models.BooleanField(default=False, verbose_name='Wheelchair Accessible')

    # Photo
    photo = models.ImageField(upload_to='court_photos/', blank=True, null=True)

    # Ownership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courts',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.city}'

    def amenities_list(self):
        """Return a list of available amenities."""
        amenities = []
        if self.has_lighting:
            amenities.append('Lighting')
        if self.has_parking:
            amenities.append('Parking')
        if self.has_restrooms:
            amenities.append('Restrooms')
        if self.has_equipment_rental:
            amenities.append('Equipment Rental')
        if self.has_water_fountain:
            amenities.append('Water Fountain')
        if self.has_seating:
            amenities.append('Spectator Seating')
        if self.is_wheelchair_accessible:
            amenities.append('Wheelchair Accessible')
        return amenities

    def average_rating(self):
        """Return the average review rating or None."""
        reviews = self.reviews.all()
        if not reviews.exists():
            return None
        total = sum(r.rating for r in reviews)
        return round(total / reviews.count(), 1)

    def review_count(self):
        return self.reviews.count()


class CourtReview(models.Model):
    """A user review for a court they have visited."""
    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='court_reviews',
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rate from 1 (poor) to 5 (excellent)',
    )
    comment = models.TextField(
        blank=True,
        help_text='Share your experience at this court',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('court', 'user')  # one review per user per court

    def __str__(self):
        return f'{self.user.username} — {self.rating}/5 — {self.court.name}'


class FavoriteCourt(models.Model):
    """A user's saved favorite court."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_courts',
    )
    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE,
        related_name='favorited_by',
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'court')
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.user.username} — {self.court.name}'


class CourtReport(models.Model):
    """A report of inaccurate or outdated court information."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        REVIEWED = 'REVIEWED', 'Reviewed'
        RESOLVED = 'RESOLVED', 'Resolved'
        DISMISSED = 'DISMISSED', 'Dismissed'

    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE,
        related_name='reports',
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_submitted',
    )
    reason = models.TextField(help_text='Describe what information is inaccurate or outdated.')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Report on "{self.court.name}" by {self.reported_by.username}'

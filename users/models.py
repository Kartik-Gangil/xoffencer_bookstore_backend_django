from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models

class CustomUser(AbstractUser):
    # These are the roles a person can have in the system
    ROLE_CHOICES = (
        ("author", "Author"),
        ("editor", "Editor"),
        ("contributor", "Contributor"),
        ("customer", "Customer"), # A standard user who buys books
        ("admin", "Admin"),
    )
    
    # We extend the built-in User with new fields from your spreadsheet/screenshots
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
    designation = models.CharField(max_length=255, blank=True, null=True)
    university_organization = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_image_url = models.URLField(max_length=500, blank=True, null=True) # For author photo
    
    # Author-specific fields
    orcid = models.CharField(max_length=100, blank=True, null=True)
    social_media_link = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        # This helps identify the user in the admin panel
        return f"{self.username} ({self.role})"
    
class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=255)
    address_line_1 = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False) # To mark one address as the primary

    def __str__(self):
        return f"{self.full_name}, {self.address_line_1}, {self.city}"
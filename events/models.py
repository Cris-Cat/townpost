# File: events/models.py

import secrets
from django.db import models
from django.utils.text import slugify
from datetime import timedelta
from django.utils import timezone

class Category(models.Model):
    """
    Category Model
    --------------
    Purpose: Groups events into logical buckets (e.g., Music, Sports).
    Technical Points: 
    - Uses a unique slug for clean URL routing.
    - Includes an optional emoji for UI display.
    Edge Cases: 
    - If a slug is not provided, it auto-generates one from the name.
    - If a duplicate slug exists, it appends a counter (e.g., music-1).
    """
    name = models.CharField(max_length=50, unique=True, help_text="Category name")
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    emoji = models.CharField(max_length=10, blank=True, default="", help_text="Optional visual icon")

    def save(self, *args, **kwargs):
        # Auto-generate slug if it's empty
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # Edge case: prevent duplicate slugs by appending a number
            while self.__class__.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        # Strip ensures we don't return a leading space if emoji is empty
        return f"{self.emoji} {self.name}".strip()

# File: events/models.py



# --- NEW MODELS FOR LOCATION ---
class Country(models.Model):
    """
    Country Model
    -------------
    Purpose: Stores countries. Admin can add more via Django admin.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class City(models.Model):
    """
    City Model
    ------------
    Purpose: Stores cities linked to a country.
    """
    name = models.CharField(max_length=100, unique=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='cities')
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class Event(models.Model):
    """
    Event Model
    -----------
    Purpose: The core entity representing a local notice or happening.
    Technical Points: 
    - Tracks moderation status (pending/approved/rejected/archived).
    - Generates a secure, random token for passwordless editing.
    - Supports both dated events (Weekly Board) and dateless events (Info Board).
    Edge Cases: 
    - Auto-generates a unique slug.
    - Generates the edit token ONLY once upon creation to prevent link leakage.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]

    # Basic Info
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    description = models.TextField(help_text="Max 500 words")
    
    pending_title = models.CharField(max_length=200, blank=True, default="")
    pending_description = models.TextField(blank=True, default="")
    pending_start_date = models.DateField(blank=True, null=True)
    
    # PROTECT prevents deleting a Category if it has Events attached to it
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='events')
    
    # Location details
    country = models.ForeignKey(Country, on_delete=models.PROTECT, blank=True, null=True, help_text="Select country")
    city = models.ForeignKey(City, on_delete=models.PROTECT, blank=True, null=True, help_text="Select city")
    street_address = models.CharField(max_length=200, blank=True, default="", help_text="Street and house number")
    zip_code = models.CharField(max_length=20, blank=True, default="", help_text="Postal/Zip code")
    maps_url = models.URLField(blank=True, default="", help_text="Google Maps link (optional)")
    event_url = models.URLField(blank=True, default="", help_text="Link to ticket page or external event site") # <-- ADD THIS

    # Date and Time (Optional for Info Board posts)
    start_date = models.DateField(blank=True, null=True, help_text="Leave blank for Info Board")
    end_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    
    # Moderation and Security
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    secret_edit_token = models.CharField(max_length=64, unique=True, blank=True, null=True)
    consent_given = models.BooleanField(default=False)
    
    
    edit_count = models.PositiveIntegerField(default=0, help_text="Number of times this post has been edited")
    edit_token_expires_at = models.DateTimeField(blank=True, null=True, help_text="Edit link expires 7 days after creation")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-generate unique slug if empty
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while self.__class__.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            
        # Generate secret edit token ONLY when the event is first created (no primary key yet)
        if not self.pk and not self.secret_edit_token:
            # token_urlsafe(32) creates a highly secure, URL-safe 43-character string
            self.secret_edit_token = secrets.token_urlsafe(32)
            self.edit_token_expires_at = timezone.now() + timedelta(days=7)
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title




def event_image_upload_path(instance, filename):
    """
    Generates a dynamic upload path for event images.
    Organizes files into folders based on the parent Event's ID.
    
    Technical Points:
    - 'instance' is the EventImage object being saved.
    - 'instance.event' gets the parent Event object.
    - 'instance.event.id' gets the database primary key (e.g., 1, 2, 3).
    - Example output: 'events/post_12/my_photo.jpg'
    """
    return f'events/post_{instance.event.id}/{filename}'


class EventImage(models.Model):
    """
    EventImage Model
    ----------------
    Purpose: Stores photos attached to an event.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    
    # CHANGE THIS LINE: Replace the old string with our new function
    image = models.ImageField(upload_to=event_image_upload_path) 
    
    order = models.PositiveIntegerField(default=1, help_text="Display order (1-5)")
    alt_text = models.CharField(max_length=100, blank=True, default="", help_text="For accessibility")

    is_approved = models.BooleanField(default=False, help_text="Visible to public only when approved by admin.")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.event.title} (Order: {self.order})"

# File: events/models.py


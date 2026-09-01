# File: events/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Event, EventImage, Country, City

class EventImageInline(admin.TabularInline):
    """
    EventImage Inline Admin
    -----------------------
    Purpose: Allows managing images directly on the Event admin page.
    Technical Points: 
    - Added a custom 'image_preview' method to show thumbnails.
    - 'readonly_fields' prevents the preview from being treated as an editable input.
    - 'extra = 0' because we handle the minimum 3 photos on the frontend form, 
      so the admin doesn't need to show 3 empty upload slots by default.
    """
    model = EventImage
    extra = 0
    # Order of fields in the admin table
    fields = ('image_preview', 'image', 'order', 'alt_text')
    readonly_fields = ('image_preview',)

    @admin.display(description='Preview')
    def image_preview(self, obj):
        """
        Generates an HTML image tag for the admin interface.
        Edge Case: If the image file was deleted from the server but still exists in the DB,
        this safely returns a dash instead of crashing.
        """
        if obj.image:
            # format_html is CRITICAL: it safely escapes the URL to prevent XSS attacks
            # and tells Django to render the string as actual HTML, not text.
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px; border: 1px solid #ccc;" />',
                obj.image.url
            )
        return "-"

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'slug')
    list_filter = ('country',)
    prepopulated_fields = {'slug': ('name',)}
    
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'emoji')
    prepopulated_fields = {'slug': ('name',)}
    

# File: events/admin.py

# File: events/admin.py

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'start_date', 'created_at')
    list_filter = ('status', 'category', 'start_date')
    search_fields = ('title', 'description', 'location_name')
    readonly_fields = ('slug', 'secret_edit_token', 'created_at', 'updated_at')
    inlines = [EventImageInline]
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # If the admin sets the event to 'approved', apply the pending changes
        if obj.status == 'approved':
            if obj.pending_title:
                obj.title = obj.pending_title
                obj.pending_title = "" # Clear the pending field
            if obj.pending_description:
                obj.description = obj.pending_description
                obj.pending_description = "" # Clear the pending field
            if obj.pending_start_date:
                obj.start_date = obj.pending_start_date
                obj.pending_start_date = None # Clear the pending field
            obj.save() # Save the newly applied public fields
            
            # Also approve the images
            obj.images.update(is_approved=True)
            
    @admin.action(description="Mark selected events as approved")
    def make_approved(self, request, queryset):
        updated_count = queryset.update(status='approved')
        # Also approve the images for these events
        for event in queryset:
            event.images.update(is_approved=True)
        self.message_user(request, f'{updated_count} event(s) and their images successfully approved.')
        
    actions = [make_approved]
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Event, EventImage

class EventImageInline(admin.TabularInline):
    """
    EventImage Inline Admin
    -----------------------
    Purpose: Allows managing images directly on the Event admin page.
    """
    model = EventImage
    extra = 0
    fields = ('image_preview', 'image', 'order', 'alt_text')
    readonly_fields = ('image_preview',)

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px; border: 1px solid #ccc;" />',
                obj.image.url
            )
        return "-"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'emoji')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # Added country and city to list display so you can see them at a glance
    list_display = ('title', 'category', 'status', 'is_pinned', 'country', 'city', 'created_at')
    list_editable = ('status', 'is_pinned')
    list_filter = ('status', 'category', 'is_pinned', 'country', 'city')
    
    # Fixed: 'location_name' doesn't exist, replaced with country and city
    search_fields = ('title', 'description', 'country', 'city')
    readonly_fields = ('slug', 'secret_edit_token', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'category', 'is_pinned')
        }),
        ('Current Location', {
            'fields': ('country', 'city', 'street_address', 'zip_code', 'maps_url', 'event_url')
        }),
        ('Pending Changes', {
            'fields': ('pending_title', 'pending_description', 'pending_start_date', 'pending_country', 'pending_city'),  
            'description': 'Changes awaiting approval. Approving the event will apply these.'
        }),
        ('Moderation', {
            'fields': ('status',),
            'description': 'Change the status of this event (e.g., Approved, Rejected, Archived).'
        }),
    ) # Fixed missing closing parenthesis
    
    inlines = [EventImageInline]
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # If the admin sets the event to 'approved', apply the pending changes
        if obj.status == 'approved':
            if obj.pending_title:
                obj.title = obj.pending_title
                obj.pending_title = ""
            if obj.pending_description:
                obj.description = obj.pending_description
                obj.pending_description = ""
            if obj.pending_start_date:
                obj.start_date = obj.pending_start_date
                obj.pending_start_date = None
                
            # NEW: Apply pending country and city
            if obj.pending_country:
                obj.country = obj.pending_country
                obj.pending_country = ""
            if obj.pending_city:
                obj.city = obj.pending_city
                obj.pending_city = ""
                
            obj.save() # Save the newly applied public fields
            obj.images.update(is_approved=True) # Approve images
            
    @admin.action(description="Mark selected events as approved")
    def make_approved(self, request, queryset):
        for event in queryset:
            event.status = 'approved'
            
            # Apply all pending changes
            if event.pending_title:
                event.title = event.pending_title
                event.pending_title = ""
            if event.pending_description:
                event.description = event.pending_description
                event.pending_description = ""
            if event.pending_start_date:
                event.start_date = event.pending_start_date
                event.pending_start_date = None
            if event.pending_country:
                event.country = event.pending_country
                event.pending_country = ""
            if event.pending_city:
                event.city = event.pending_city
                event.pending_city = ""
                
            event.save()
            event.images.update(is_approved=True)
            
        self.message_user(request, f'{queryset.count()} event(s) and their images successfully approved.')
        
    actions = [make_approved]
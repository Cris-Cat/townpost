# File: events/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Event

# --- CUSTOM WIDGET AND FIELD FOR MULTIPLE FILES ---
class MultipleFileInput(forms.FileInput):
    """
    Custom Widget for multiple file selection.
    Overrides value_from_datadict to return a list of files.
    """
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        # CRITICAL: Return all files uploaded under this field name as a list
        return files.getlist(name)


class MultipleFileField(forms.FileField):
    """
    Custom Field to handle multiple file uploads.
    Overrides clean() to accept a list of files instead of a single file.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        # data is now a list of files (from value_from_datadict)
        # We skip the default single-file validation and just return the list
        # so our custom clean_images() can validate them.
        if not data and self.required:
            raise ValidationError(self.error_messages['required'], code='required')
        return data


class EventForm(forms.ModelForm):
    """
    Event Submission Form (Phase 2)
    -------------------------------
    Purpose: Captures event details, multiple photos, and legal consent.
    """
    
    # Use our custom MultipleFileField instead of forms.FileField
    images = MultipleFileField(
        required=False, 
        label="Upload 3 to 5 Photos (JPG, PNG, or WebP, max 5MB each)"
    )
    
    consent_given = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must confirm ownership and consent to proceed.'},
        label="I confirm I own these photos and there are no identifiable faces or copyright issues."
    )

    class Meta:
        model = Event
        # ADD the new location fields to the list
        fields = [
            'title', 'category', 'description', 'start_date', 
            'country', 'city', 'street_address', 'zip_code', 'maps_url', 'event_url',
            'consent_given'
        ]
        
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={
                'rows': 6, 
                'placeholder': 'Tell us about your event... (Max 500 words)',
                'id': 'id_description' 
            }),
            # Add basic styling to the new fields
            'street_address': forms.TextInput(attrs={'placeholder': 'e.g. Friedrichstraße 123'}),
            'zip_code': forms.TextInput(attrs={'placeholder': 'e.g. 10117'}),
            'maps_url': forms.URLInput(attrs={'placeholder': 'https://maps.google.com/...'}),
            'event_url': forms.URLInput(attrs={'placeholder': 'https://eventbrite.com/...'}),

        }

    def clean_description(self):
        """
        Validates that the description does not exceed 500 words.
        """
        description = self.cleaned_data.get('description')
        if description:
            word_count = len(description.split())
            if word_count > 500:
                raise ValidationError(f"Description must be 500 words or less. You entered {word_count} words.")
        return description

    def clean_images(self):
        """
        Validates the uploaded images for count, file type, and file size.
        """
        # Get the list of files from cleaned_data (populated by our custom MultipleFileField)
        images = self.cleaned_data.get('images') or []
        
        if len(images) < 3:
            raise ValidationError("Please upload at least 3 photos.")
        if len(images) > 5:
            raise ValidationError("You can upload a maximum of 5 photos.")
            
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        
        for img in images:
            if img.content_type not in allowed_types:
                raise ValidationError(f"File '{img.name}' is not a supported format. Please use JPG, PNG, or WebP.")
            
            if img.size > max_size:
                raise ValidationError(f"File '{img.name}' is too large. Maximum size is 5MB.")
                
        return images
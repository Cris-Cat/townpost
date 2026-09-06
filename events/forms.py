import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Event

# --- CUSTOM WIDGET AND FIELD FOR MULTIPLE FILES ---
class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True
    def value_from_datadict(self, data, files, name):
        return files.getlist(name)

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data and self.required:
            raise ValidationError(self.error_messages['required'], code='required')
        return data

class EventForm(forms.ModelForm):
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
        fields = [
            'title', 'category', 'description', 'start_date', 
            'country', 'city', 'street_address', 'zip_code', 'maps_url', 'event_url',
            'consent_given'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'id': 'id_title', 
                'maxlength': 60,
                'placeholder': 'Enter event title (max 60 characters)'
            }),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={
                'rows': 6, 
                'placeholder': 'Tell us about your event... (Max 700 char)',
                'id': 'id_description' 
            }),
            'street_address': forms.TextInput(attrs={'placeholder': 'e.g. Friedrichstraße 123'}),
            'zip_code': forms.TextInput(attrs={'placeholder': 'e.g. 10117'}),
            'maps_url': forms.URLInput(attrs={'placeholder': 'https://maps.google.com/...'}),
            'event_url': forms.URLInput(attrs={'placeholder': 'https://evente.com/...'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        
        # 1. Limit to 60 characters
        if len(title) > 60:
            raise ValidationError("Title cannot exceed 60 characters.")
            
        # 2. Sanitize with Regex (Letters, numbers, spaces, punctuation, symbols, emojis)
        # \W matches any non-word character (covers punctuation, symbols, and emojis)
        if not re.match(r'^[a-zA-Z0-9\s\W]+$', title):
            raise ValidationError("Title contains invalid characters. Only letters, numbers, punctuation, and emojis are allowed.")
            
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        
        if description:
            # 1. Character count limit (Changed from 500 words to 700 characters)
            char_count = len(description)
            if char_count > 700:
                raise ValidationError(f"Description must be 700 characters or less. You entered {char_count} characters.")
                
            # 2. Sanitize with Regex (Allows newlines \n for paragraphs)
            if not re.match(r'^[a-zA-Z0-9\s\n\W]+$', description):
                raise ValidationError("Description contains invalid characters. Only letters, numbers, punctuation, and emojis are allowed.")
                
        return description

    def clean_images(self):
        images = self.files.getlist('images')
        if not images:
            return images
            
        is_edit = self.instance.pk is not None
        min_photos = 1 if is_edit else 3
        
        if len(images) < min_photos:
            raise ValidationError(f"Please upload at least {min_photos} photos.")
        if len(images) > 5:
            raise ValidationError("You can upload a maximum of 5 photos.")
            
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        max_size = 5 * 1024 * 1024  # 5MB
        
        for img in images:
            if img.content_type not in allowed_types:
                raise ValidationError(f"File '{img.name}' is not a supported format. Please use JPG, PNG, or WebP.")
            if img.size > max_size:
                raise ValidationError(f"File '{img.name}' is too large. Maximum size is 5MB.")
                
        return images
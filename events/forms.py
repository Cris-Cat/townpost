import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Event
from .utils import get_location_data

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
        label="Upload 1 to 5 Photos (JPG, PNG, or WebP, max 5MB each)"
    )
    consent_given = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must confirm ownership and consent to proceed.'},
        label="I confirm I own these photos and there are no identifiable faces or copyright issues."
    )

    # Explicitly define country and city as ChoiceFields
    country = forms.ChoiceField(required=False, label="Country", choices=[])
    city = forms.ChoiceField(required=False, label="City", choices=[])

    class Meta:
        model = Event
        fields = [
            'title', 'category', 'description', 'start_date', 'end_date',
            'country', 'city', 'street_address', 'zip_code', 'maps_url', 'event_url',
            'consent_given'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'id': 'id_start_date'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'id': 'id_end_date'}),
            'description': forms.Textarea(attrs={
                'rows': 6, 
                'placeholder': 'Tell us about your event... (Max 700 characters)',
                'id': 'id_description' 
            }),
            'street_address': forms.TextInput(attrs={'placeholder': 'e.g. Friedrichstraße 123'}),
            'zip_code': forms.TextInput(attrs={'placeholder': 'e.g. 10117'}),
            'maps_url': forms.URLInput(attrs={'placeholder': 'https://maps.google.com/...'}),
            'event_url': forms.URLInput(attrs={'placeholder': 'https://eventbrite.com/...'}),
            'country': forms.Select(attrs={'id': 'id_country'}),
            'city': forms.Select(attrs={'id': 'id_city'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Load data from JSON
        country_choices, self.city_data = get_location_data()
        
        # 2. Populate the Country dropdown
        self.fields['country'].choices = country_choices
        
        # 3. DYNAMIC CITY VALIDATION (The Fix!)
        # If the form is being submitted (POST), 'self.data' contains the submitted country.
        if self.data and self.data.get('country'):
            selected_country = self.data.get('country')
            if selected_country in self.city_data:
                cities = self.city_data[selected_country]
                city_choices = [('', 'Select a city')] + [(city, city) for city in cities]
                self.fields['city'].choices = city_choices
                
        # 4. If editing an existing event (GET request with an instance), pre-populate cities
        elif self.instance and self.instance.pk and self.instance.country:
            country_name = self.instance.country
            if country_name in self.city_data:
                cities = self.city_data[country_name]
                city_choices = [('', 'Select a city')] + [(city, city) for city in cities]
                
                # Ensure the saved city is in the choices (in case it was typed manually)
                if self.instance.city and self.instance.city not in [c[0] for c in city_choices]:
                    city_choices.append((self.instance.city, self.instance.city))
                    
                self.fields['city'].choices = city_choices

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if description:
            char_count = len(description)
            if char_count > 700:
                raise ValidationError(f"Description must be 700 characters or less. You entered {char_count} characters.")
            if not re.match(r'^[a-zA-Z0-9\s\n\W]+$', description):
                raise ValidationError("Description contains invalid characters. Only letters, numbers, spaces, punctuation, and emojis are allowed.")
        return description

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) > 60:
            raise ValidationError("Title cannot exceed 60 characters.")
        if not re.match(r'^[a-zA-Z0-9\s\W]+$', title):
            raise ValidationError("Title contains invalid characters. Only letters, numbers, spaces, punctuation, and emojis are allowed.")
        return title

    def clean_images(self):
        images = self.files.getlist('images')
        if not images:
            return images
        if len(images) < 1:
            raise ValidationError("Please upload at least 1 photo.")
        if len(images) > 5:
            raise ValidationError("You can upload a maximum of 5 photos.")
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        max_size = 5 * 1024 * 1024
        for img in images:
            if img.content_type not in allowed_types:
                raise ValidationError(f"File '{img.name}' is not a supported format.")
            if img.size > max_size:
                raise ValidationError(f"File '{img.name}' is too large. Maximum size is 5MB.")
        return images
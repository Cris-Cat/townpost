# File: events/views.py

from django.shortcuts import render, redirect, get_object_or_404
from .models import Event, EventImage
from .forms import EventForm
from .utils import process_and_strip_exif 


def home_view(request):
    # ... (keep this exactly as it was) ...
    events = Event.objects.filter(status='approved').order_by('-start_date', 'title')
    return render(request, 'events/home.html', {'events': events})


def submit_event_view(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        
        if form.is_valid():
            # 1. Save the main Event object first
            event = form.save()
            
            # 2. Retrieve the validated list of images
            images = form.cleaned_data.get('images')
            
            # 3. Loop through images, PROCESS them, and save
            for index, image in enumerate(images, start=1):
                # --- NEW: Process the image (resize + strip EXIF) ---
                processed_image_file = process_and_strip_exif(image)
                
                # 4. Save to the EventImage model
                EventImage.objects.create(
                    event=event,
                    image=processed_image_file, # <-- Save the processed file, not the raw one
                    order=index,
                )
                
            return redirect('home')
    else:
        form = EventForm()
        
    return render(request, 'events/submit.html', {'form': form})
    

def event_detail_view(request, slug):
    # ... (keep this exactly as it was) ...
    event = get_object_or_404(Event, slug=slug, status='approved')
    return render(request, 'events/event_detail.html', {'event': event})
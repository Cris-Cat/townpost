# File: events/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Event, EventImage
from .forms import EventForm
from .utils import process_and_strip_exif, get_week_range  # <-- Added get_week_range

def home_view(request):
    """
    Home Page View (Weekly Board)
    -----------------------------
    Purpose: Displays ONLY approved events happening in the CURRENT week.
    Technical Points:
    - Gets the Monday and Sunday of the current week.
    - Filters events where start_date falls between Monday and Sunday (inclusive).
    - Excludes events with no start_date (those belong on the Info Board).
    - Orders by start_date, then by title.
    """
    monday, sunday = get_week_range()
    
    # Filter: approved, has a start date, and falls within this week's range
    events = Event.objects.filter(
        status='approved',
        start_date__isnull=False,
        start_date__gte=monday,
        start_date__lte=sunday
    ).order_by('start_date', 'title')
    
    return render(request, 'events/home.html', {
        'events': events,
        'week_start': monday,
        'week_end': sunday
    })


def info_board_view(request):
    """
    Info Board View
    ---------------
    Purpose: Displays approved events that do NOT have a specific date (e.g., Notices).
    Technical Points:
    - Filters for approved events where start_date is NULL.
    - Orders by creation date (newest first).
    """
    events = Event.objects.filter(
        status='approved',
        start_date__isnull=True
    ).order_by('-created_at')
    
    return render(request, 'events/info_board.html', {'events': events})


def submit_event_view(request):
    # ... (keep this exactly as it is) ...
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            images = form.cleaned_data.get('images')
            for index, image in enumerate(images, start=1):
                processed_image_file = process_and_strip_exif(image)
                EventImage.objects.create(
                    event=event,
                    image=processed_image_file,
                    order=index,
                )
            return redirect('home')
    else:
        form = EventForm()
    return render(request, 'events/submit.html', {'form': form})


def event_detail_view(request, slug):
    # ... (keep this exactly as it is) ...
    event = get_object_or_404(Event, slug=slug, status='approved')
    return render(request, 'events/event_detail.html', {'event': event})
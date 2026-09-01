# File: events/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Event, EventImage
from .forms import EventForm
from .utils import process_and_strip_exif, get_week_range  # <-- Added get_week_range
from .models import Event, EventImage, Category 


def home_view(request):
    """
    Home Page View (Weekly Board with Filters & Show All)
    -----------------------------------------------------
    """
    # 1. Check if user clicked "Show All"
    show_all = request.GET.get('view') == 'all'
    
    if show_all:
        # If Show All is active, get the 20 most recent approved events.
        # We remove the date filter so it includes both Dated events and Notices.
        events = Event.objects.filter(status='approved').order_by('-created_at')[:20]
        
    else:
        # 2. Standard Logic (This Week + Filters)
        monday, sunday = get_week_range()
        
        # Base queryset: approved and has a start date
        events = Event.objects.filter(
            status='approved',
            start_date__isnull=False
        )
        
        # Apply Date Filters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date and end_date:
            events = events.filter(start_date__gte=start_date, start_date__lte=end_date)
        else:
            # Default to current week if no custom dates
            events = events.filter(start_date__gte=monday, start_date__lte=sunday)
            
        # Apply Category Filter
        category_slug = request.GET.get('category')
        if category_slug:
            events = events.filter(category__slug=category_slug)
            
        # Order by date
        events = events.order_by('start_date', 'title')

    # 3. Get categories for the dropdown
    categories = Category.objects.all().order_by('name')
    
    return render(request, 'events/home.html', {
        'events': events,
        'categories': categories,
        'week_start': get_week_range()[0],
        'week_end': get_week_range()[1],
        'is_show_all': show_all 
    })

# ... (keep submit_event_view and event_detail_view exactly as they are) ...

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
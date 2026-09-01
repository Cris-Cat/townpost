# File: events/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Event, EventImage, Category
from .forms import EventForm
from django.http import JsonResponse
from .utils import process_and_strip_exif, get_week_range

def home_view(request):
    """
    Home Page View (Weekly Board with Filters & Show All)
    """
    show_all = request.GET.get('view') == 'all'
    
    if show_all:
        events = Event.objects.filter(status='approved').order_by('-created_at')[:20]
    else:
        monday, sunday = get_week_range()
        events = Event.objects.filter(status='approved', start_date__isnull=False)
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date and end_date:
            events = events.filter(start_date__gte=start_date, start_date__lte=end_date)
        else:
            events = events.filter(start_date__gte=monday, start_date__lte=sunday)
            
        category_slug = request.GET.get('category')
        if category_slug:
            events = events.filter(category__slug=category_slug)
            
        events = events.order_by('start_date', 'title')

    categories = Category.objects.all().order_by('name')
    
    return render(request, 'events/home.html', {
        'events': events,
        'categories': categories,
        'week_start': get_week_range()[0],
        'week_end': get_week_range()[1],
        'is_show_all': show_all
    })


def info_board_view(request):
    """
    Info Board View (Dateless Notices)
    """
    events = Event.objects.filter(status='approved', start_date__isnull=True).order_by('-created_at')
    return render(request, 'events/info_board.html', {'events': events})


def submit_event_view(request):
    """
    Submit Event View
    """
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
            return redirect('submit_success', token=event.secret_edit_token)
    else:
        form = EventForm()
    return render(request, 'events/submit.html', {'form': form})


def submit_success_view(request, token):
    """
    Success Page View
    """
    try:
        event = Event.objects.get(secret_edit_token=token)
    except Event.DoesNotExist:
        return redirect('home')
    return render(request, 'events/success.html', {'event': event})



def secret_edit_view(request, token):
    try:
        event = Event.objects.get(secret_edit_token=token)
    except Event.DoesNotExist:
        return redirect('home')
        
    if event.status in ['rejected', 'archived']:
        return render(request, 'events/edit_denied.html')

    if request.method == 'POST':
        print("=== FORM SUBMITTED ===")
        
        # We pass instance=event so the form validates, but we DO NOT call form.save()
        form = EventForm(request.POST, request.FILES, instance=event)
        
        if form.is_valid():
            print("Form is valid!")
            print("New text from form:", form.cleaned_data['description'])

            # 1. MANUALLY assign new text to PENDING fields only.
            event.pending_title = form.cleaned_data['title']
            event.pending_description = form.cleaned_data['description']
            event.pending_start_date = form.cleaned_data['start_date']
            
            # Set status to pending
            event.status = 'pending'
            
           
            # Write directly to DB, bypassing all signals/hooks
            Event.objects.filter(pk=event.pk).update(
                pending_title=event.pending_title,
                pending_description=event.pending_description,
                pending_start_date=event.pending_start_date,
                status=event.status
            )
            
            print("Event saved successfully via update()!")
            
            # 2. Handle Photo Deletions
            deleted_ids_str = request.POST.get('deleted_image_ids', '')
            if deleted_ids_str:
                ids_to_delete = [int(x) for x in deleted_ids_str.split(',') if x.isdigit()]
                event.images.filter(id__in=ids_to_delete).delete()
            
            # 3. Handle New Photo Uploads
            new_images = form.cleaned_data.get('images')
            if new_images:
                for index, image in enumerate(new_images, start=1):
                    processed_image_file = process_and_strip_exif(image)
                    EventImage.objects.create(
                        event=event,
                        image=processed_image_file,
                        order=index,
                        is_approved=False
                    )
                    
            return JsonResponse({'success': True})
        else:
            print("Form is INVALID. Errors:", form.errors)
    else:
        form = EventForm(instance=event)
        
    existing_images_data = [
        {'id': img.id, 'name': img.image.name.split('/')[-1], 'preview': img.image.url, 'size': 0, 'isExisting': True}
        for img in event.images.all()
    ]
        
    return render(request, 'events/edit.html', {
        'form': form, 
        'event': event,
        'existing_images_data': existing_images_data
    })


def event_detail_view(request, slug):
    event = get_object_or_404(Event, slug=slug)
    
    if event.status in ['rejected', 'archived']:
        return render(request, 'events/event_unavailable.html', {'event': event})
        
    # --- CHANGE THIS: Only get images that the admin has approved ---
    approved_images = event.images.filter(is_approved=True)
        
    return render(request, 'events/event_detail.html', {
        'event': event,
        'approved_images': approved_images # Pass this to the template
    })
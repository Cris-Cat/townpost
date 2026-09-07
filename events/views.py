# File: events/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Event, EventImage, Category
from .forms import EventForm
from django.http import JsonResponse
from .utils import process_and_strip_exif, get_week_range
from altcha import ChallengeOptionsV1, create_challenge_v1
from altcha import verify_solution
from django.conf import settings
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
import calendar
from datetime import datetime, timedelta, date

def home_view(request):
    view_type = request.GET.get('view', 'this_week')
    start_date_param = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    month_param = request.GET.get('month')
    
    # NEW: Custom Ribbon Filters
    category_param = request.GET.get('category')
    from_date_param = request.GET.get('from_date')
    to_date_param = request.GET.get('to_date')

    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    title = "This Week's Events"

    # 1. Base Query Logic
    if view_type == 'all':
        events_list = Event.objects.filter(status='approved').order_by('-is_pinned', '-created_at')
        title = "All Active Submissions"
        
    elif view_type == 'upcoming' and start_date_param and end_date_param:
        s_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
        e_date = datetime.strptime(end_date_param, '%Y-%m-%d').date() + timedelta(days=1)
        events_list = Event.objects.filter(status='approved', start_date__gte=s_date, start_date__lt=e_date).order_by('-is_pinned', 'start_date')
        title = f"Schedule: {s_date.strftime('%b %d')} – {(e_date - timedelta(days=1)).strftime('%b %d')}"
        week_start, week_end = s_date, e_date - timedelta(days=1)
        
    elif view_type == 'past' and month_param:
        try:
            year, month = map(int, month_param.split('-'))
            first_day = date(year, month, 1)
            last_day = date(year, month, calendar.monthrange(year, month)[1])
            events_list = Event.objects.filter(status='approved', created_at__date__gte=first_day, created_at__date__lte=last_day).order_by('-is_pinned', '-created_at')
            title = f"Past Events: {first_day.strftime('%B %Y')}"
            week_start, week_end = first_day, last_day
        except Exception:
            events_list = Event.objects.none()
            title = "Invalid Month"
            
    else: # Default: This Week (by submission date)
        events_list = Event.objects.filter(status='approved', created_at__date__gte=week_start, created_at__date__lte=week_end).order_by('-is_pinned', '-created_at')
        title = f"This Week ({week_start.strftime('%b %d')}-{week_end.strftime('%d')})"

    # 2. Apply Custom Ribbon Filters (Overrides date logic if dates are provided)
    if category_param:
        events_list = events_list.filter(category__name__iexact=category_param)
        
    if from_date_param or to_date_param:
        # If user uses the ribbon dates, we filter by EVENT date (start_date), not submission date
        if from_date_param:
            events_list = events_list.filter(start_date__gte=from_date_param)
        if to_date_param:
            events_list = events_list.filter(start_date__lte=to_date_param)
            
        # Update title to reflect custom search
        title = "Custom Search Results"
        if from_date_param and to_date_param:
            title = f"Events from {from_date_param} to {to_date_param}"
        elif from_date_param:
            title = f"Events after {from_date_param}"
        elif to_date_param:
            title = f"Events before {to_date_param}"

    # Pagination
    paginator = Paginator(events_list, 30)
    page_number = request.GET.get('page')
    events = paginator.get_page(page_number)
    
    return render(request, 'events/home.html', {
        'events': events,
        'is_show_all': (view_type == 'all'),
        'week_start': week_start,
        'week_end': week_end,
        'display_title': title,
    })


def info_board_view(request):
    """
    Info Board View (Notices)
    -------------------------
    Purpose: Shows only active 'Notice' category posts from the last 30 days.
    """
    # Calculate the date 30 days ago
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Filter by: Approved, Category is 'Notice', and Submitted in the last 30 days
    events = Event.objects.filter(
        status='approved',
        category__name__iexact='Notice',  # Matches 'Notice', 'notice', 'NOTICE'
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')
    
    return render(request, 'events/info_board.html', {'events': events})

import json
from django.shortcuts import render, redirect
from django.conf import settings
# ... keep your other imports like EventForm, EventImage, process_and_strip_exif, verify_solution ...

def submit_event_view(request):
    """
    Submit Event View
    """
    if request.method == 'POST':
        # --- ALTCHA VERIFICATION ---
        altcha_payload = request.POST.get('altcha', '')

        if not altcha_payload:
            form = EventForm(request.POST, request.FILES)
            form.add_error(None, 'Captcha verification failed. Please try again.')
            return render(request, 'events/submit.html', {
                'form': form,
                'city_data_json': json.dumps(form.city_data)
            })
        
        is_valid = verify_solution(altcha_payload, settings.ALTCHA_HMAC_SECRET)
        if not is_valid:
            form = EventForm(request.POST, request.FILES)
            form.add_error(None, 'Captcha verification failed. Please refresh the page and try again.')
            return render(request, 'events/submit.html', {
                'form': form,
                'city_data_json': json.dumps(form.city_data)
            })
        # --- END ALTCHA VERIFICATION ---

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
            print("SUBMIT FORM REJECTED! ERRORS:", form.errors) 


        # If the form is invalid (e.g. title too long), reload page with errors AND city data
            return render(request, 'events/submit.html', {
                'form': form,
                'city_data_json': json.dumps(form.city_data)
            })

    else:
        # GET request: Show empty form with city data
        form = EventForm()

    return render(request, 'events/submit.html', {
        'form': form,
        'city_data_json': json.dumps(form.city_data)
    })

def submit_success_view(request, token):
    """
    Success Page View
    """
    try:
        event = Event.objects.get(secret_edit_token=token)
    except Event.DoesNotExist:
        return redirect('home')
    
    # Calculate remaining edits (Max 5)
    remaining_edits = 5 - event.edit_count
    
    return render(request, 'events/success.html', {
        'event': event,
        'remaining_edits': remaining_edits
    })
    


def secret_edit_view(request, token):
    try:
        event = Event.objects.get(secret_edit_token=token)
    except Event.DoesNotExist:
        return redirect('home')

    if event.edit_token_expires_at and timezone.now() > event.edit_token_expires_at:
        return render(request, 'events/edit_unavailable.html', {
            'reason': 'expired',
            'event': event
        })
    
    # --- CHECK 2: Has the edit limit been reached? ---
    if event.edit_count >= 5:
        return render(request, 'events/edit_unavailable.html', {
            'reason': 'limit_reached',
            'event': event
        })    
    if event.status in ['rejected', 'archived']:
        return render(request, 'events/edit_denied.html')

    if request.method == 'POST':
        # --- ALTCHA VERIFICATION ---
        altcha_payload = request.POST.get('altcha', '')
        if not altcha_payload:
            form = EventForm(request.POST, request.FILES)
            form.add_error(None, 'Captcha verification failed. Please try again.')
            return render(request, 'events/submit.html', {'form': form})
        
        is_valid = verify_solution(altcha_payload, settings.ALTCHA_HMAC_SECRET)
        if not is_valid:
            form = EventForm(request.POST, request.FILES)
            form.add_error(None, 'Captcha verification failed. Please refresh the page and try again.')
            return render(request, 'events/submit.html', {'form': form})
        # --- END ALTCHA VERIFICATION ---        
        # We pass instance=event so the form validates, but we DO NOT call form.save()
        form = EventForm(request.POST, request.FILES, instance=event)
        
        if form.is_valid():

            # 1. MANUALLY assign new text to PENDING fields only.
            event.pending_title = form.cleaned_data['title']
            event.pending_description = form.cleaned_data['description']
            event.pending_start_date = form.cleaned_data['start_date']
            event.pending_country = form.cleaned_data.get('country') 
            event.pending_city = form.cleaned_data.get('city')
            # Set status to pending
            event.status = 'pending'
            
           
            # Write directly to DB, bypassing all signals/hooks
            # Write directly to DB, bypassing all signals/hooks
            Event.objects.filter(pk=event.pk).update(
                pending_title=event.pending_title,
                pending_description=event.pending_description,
                pending_start_date=event.pending_start_date,
                status=event.status,
                edit_count=event.edit_count + 1  # Increment edit count
            )
            
            
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
    remaining_edits = max(0, 5 - event.edit_count)

    return render(request, 'events/edit.html', {
        'form': form, 
        'event': event,
        'existing_images_data': existing_images_data,
        'remaining_edits': remaining_edits,

        
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


def altcha_challenge_view(request):
    """
    Altcha Challenge Endpoint (v2.x API)
    -------------------------------------
    Purpose: Generates a proof-of-work challenge for the Altcha widget.
    """
    options = ChallengeOptionsV1(
        max_number=100000,  # Good balance: ~0.5-1 second on most devices
        expires=datetime.now() + timedelta(hours=1),  # Expires in 1 hour
        hmac_key=settings.ALTCHA_HMAC_SECRET,
    )
    challenge = create_challenge_v1(options)
    
    return JsonResponse({
        'algorithm': challenge.algorithm,
        'challenge': challenge.challenge,
        'maxnumber': challenge.max_number,
        'salt': challenge.salt,
        'signature': challenge.signature,
    })

def privacy_policy_view(request):
    """
    Privacy Policy Page
    """
    return render(request, 'events/privacy_policy.html')

def terms_of_service_view(request):
    """
    Terms of Service Page
    """
    return render(request, 'events/terms_of_service.html')
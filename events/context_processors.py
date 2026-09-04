from .utils import get_week_range, get_upcoming_weeks, get_past_months
from .models import Category # Import the Category model

def sidebar_data(request):
    current_monday, current_sunday = get_week_range()
    upcoming_weeks = get_upcoming_weeks(3)
    past_months = get_past_months(6)
    
    # Get all active categories for the filter dropdown
    categories = Category.objects.all().order_by('name')
    
    return {
        'current_week_start': current_monday,
        'current_week_end': current_sunday,
        'upcoming_weeks': upcoming_weeks,
        'past_months': past_months,
        'categories': categories, # Pass this to the template
    }
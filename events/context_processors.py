# File: events/context_processors.py

from .utils import get_week_range, get_upcoming_weeks, get_past_weeks_grouped_by_month

def sidebar_data(request):
    """
    Sidebar Context Processor
    -------------------------
    Purpose: Automatically provides navigation data to every template in the project.
    This prevents us from having to write the same sidebar logic in every single view.
    """
    # Get the current week for highlighting the active link
    current_monday, current_sunday = get_week_range()
    
    # Get the next 4 weeks for the "Upcoming" section
    upcoming_weeks = get_upcoming_weeks(4)
    
    # Get the past 6 months grouped by month/week for the "Past Events" section
    past_months = get_past_weeks_grouped_by_month(6)
    
    return {
        'current_week_start': current_monday,
        'upcoming_weeks': upcoming_weeks,
        'past_months': past_months,
    }
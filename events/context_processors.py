from .utils import get_week_range, get_upcoming_weeks, get_past_months
from .models import Category 
from .utils import get_location_data
import json
from pathlib import Path
from django.conf import settings

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



def location_filter(request):
    # Points to the 'data' folder next to your manage.py file
    json_path = Path(settings.BASE_DIR) / 'data' / 'locations.json'
    
    if not json_path.exists():
        print("!!! ERROR: locations.json not found at", json_path)
        return {'filter_countries': [], 'filter_city_map_json': '{}'}
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle the NEW dictionary format: {"Country": ["City1", "City2"]}
        if isinstance(data, dict):
            countries = list(data.keys())
            city_map = data
        else:
            # Fallback for OLD list format: [{"name": "Country", "cities": ["City1"]}]
            countries = [item.get('name') for item in data if item.get('name')]
            city_map = {item.get('name'): item.get('cities', []) for item in data if item.get('name')}
            
        return {
            'filter_countries': countries,
            'filter_city_map_json': json.dumps(city_map)
        }
    except Exception as e:
        print(f"!!! ERROR loading locations.json: {e}")
        return {'filter_countries': [], 'filter_city_map_json': '{}'}
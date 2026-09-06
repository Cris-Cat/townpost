# File: events/utils.py

import io
from PIL import Image
from django.core.files.base import ContentFile
import calendar
from datetime import date
from datetime import date
import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError

def process_and_strip_exif(image_file):
    """
    Secure Image Processing Utility
    ---------------------------------
    - Verifies the file is a real image (blocks scripts/viruses).
    - Resizes to max 1024x1024 pixels.
    - Strips all EXIF/GPS metadata.
    """
    try:
        # 1. Open and Verify the image (This blocks non-image files/scripts)
        img = Image.open(image_file)
        img.verify() 
        
        # Re-open the file because verify() consumes it
        image_file.seek(0)
        img = Image.open(image_file)
        
        # 2. Convert to RGB if necessary
        if img.mode in ("RGBA", "P", "CMYK"):
            img = img.convert("RGB")
            
        # 3. Resize to max 1024x1024 (Maintains aspect ratio)
        max_size = (1024, 1024)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 4. Save to memory buffer, stripping EXIF data
        buffer = io.BytesIO()
        # Always save as JPEG for consistency and smaller size
        img.save(buffer, format='JPEG', quality=85)
        
        # 5. Reset buffer and return
        buffer.seek(0)
        return ContentFile(buffer.getvalue(), name=image_file.name)
        
    except Exception:
        # If Pillow fails to open it, it's not a valid image
        raise ValidationError("Invalid or corrupted image file. Please upload a valid image.")

def get_week_range(target_date=None):
    if target_date is None:
        target_date = timezone.localdate()
    monday = target_date - datetime.timedelta(days=target_date.weekday())
    sunday = monday + datetime.timedelta(days=6)
    return monday, sunday

def get_upcoming_weeks(num_weeks=3):
    """Returns the NEXT 'num_weeks' weeks (excluding current week)"""
    weeks = []
    current_monday, _ = get_week_range()
    # Start from i=1 to skip the current week
    for i in range(1, num_weeks + 1):
        monday = current_monday + datetime.timedelta(weeks=i)
        sunday = monday + datetime.timedelta(days=6)
        weeks.append((monday, sunday))
    return weeks

def get_past_months(num_months=6):
    """Returns the last 'num_months' as a list of dictionaries"""
    months = []
    today = timezone.localdate()
    
    for i in range(num_months):
        year = today.year
        month = today.month - i
        
        while month <= 0:
            month += 12
            year -= 1
            
        month_key = f"{year}-{month:02d}"
        month_label = date(year, month, 1).strftime("%B %Y")
        months.append({'key': month_key, 'label': month_label})
        
    return months
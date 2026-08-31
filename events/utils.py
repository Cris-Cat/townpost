# File: events/utils.py

import io
from PIL import Image
from django.core.files.base import ContentFile

def process_and_strip_exif(image_file):
    """
    Image Processing Utility
    ------------------------
    Purpose: Resizes large images to save space and strips all EXIF/GPS metadata for privacy.
    
    Technical Points:
    - Opens the image using Pillow.
    - Converts RGBA (transparent PNGs) or CMYK to RGB, which is required for standard web formats.
    - Resizes the image to a maximum width of 1400px while maintaining the aspect ratio.
    - Saves the image to a memory buffer (BytesIO) without EXIF data.
    - Returns a Django ContentFile ready to be saved to the ImageField.
    
    Edge Cases Handled:
    - If the image is already smaller than 1400px, it skips resizing to preserve quality.
    - Safely handles different image formats (JPEG, PNG, WebP).
    """
    # 1. Open the image
    img = Image.open(image_file)
    
    # 2. Convert to RGB if necessary (e.g., PNG with transparency or CMYK JPEGs)
    # This prevents errors when saving to JPEG/WebP formats
    if img.mode in ("RGBA", "P", "CMYK"):
        img = img.convert("RGB")
    
    # 3. Resize if the width is greater than 1400px
    max_width = 1400
    if img.width > max_width:
        # Calculate the new height to maintain the aspect ratio
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        # LANCZOS is the highest quality downsampling filter in Pillow
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
    
    # 4. Save to a memory buffer, stripping EXIF data
    buffer = io.BytesIO()
    save_format = img.format or 'JPEG'
    
    if save_format == 'JPEG':
        # Saving as JPEG without the 'exif' parameter automatically strips all EXIF/GPS data
        # Quality 85 is the sweet spot: visually identical to 100, but much smaller file size
        img.save(buffer, format='JPEG', quality=85)
    else:
        # For PNG or WebP, saving without exif data also strips metadata
        img.save(buffer, format=save_format)
    
    # 5. Reset buffer pointer to the beginning
    buffer.seek(0)
    
    # 6. Return as a Django ContentFile so it can be saved to the model
    # We keep the original filename
    return ContentFile(buffer.getvalue(), name=image_file.name)

import datetime
from django.utils import timezone

def get_week_range(target_date=None):
    """
    Week Range Calculator
    ---------------------
    Purpose: Returns the Monday 00:00 and Sunday 23:59 for a given date.
    If no date is provided, it defaults to today.
    
    Technical Points:
    - Uses Python's datetime.weekday() where Monday is 0 and Sunday is 6.
    - Uses Django's timezone utilities to ensure compatibility with the database.
    """
    if target_date is None:
        target_date = timezone.localdate() # Gets today's date in the current timezone
        
    # Calculate the Monday of this week
    # If today is Wednesday (2), we subtract 2 days to get Monday (0)
    monday = target_date - datetime.timedelta(days=target_date.weekday())
    
    # Calculate the Sunday of this week
    sunday = monday + datetime.timedelta(days=6)
    
    return monday, sunday


def get_upcoming_weeks(num_weeks=4):
    """
    Upcoming Weeks Generator
    ------------------------
    Purpose: Generates a list of the next 'num_weeks' (including the current week).
    Used for the Calendar button to browse future weeks.
    """
    weeks = []
    # Start from the current week
    current_monday, _ = get_week_range()
    
    for i in range(num_weeks):
        monday = current_monday + datetime.timedelta(weeks=i)
        sunday = monday + datetime.timedelta(days=6)
        weeks.append((monday, sunday))
        
    return weeks


def get_past_weeks_grouped_by_month(num_months=3):
    """
    Past Weeks Grouping
    -------------------
    Purpose: Generates past weeks grouped by month for the Archive side panel.
    Returns a dictionary like: {'August 2023': [(mon, sun), ...], 'July 2023': [...]}
    """
    archive = {}
    current_monday, _ = get_week_range()
    
    # We go backwards. Start from last week.
    for i in range(1, num_months * 5): # 5 weeks per month approx
        monday = current_monday - datetime.timedelta(weeks=i)
        sunday = monday + datetime.timedelta(days=6)
        
        # Group by Month and Year
        month_key = monday.strftime("%B %Y") # e.g., "August 2023"
        
        if month_key not in archive:
            archive[month_key] = []
            
        archive[month_key].append((monday, sunday))
        
        # Stop if we have enough months
        if len(archive) >= num_months:
            break
            
    return archive
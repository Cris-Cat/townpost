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
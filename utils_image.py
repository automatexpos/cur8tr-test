"""
Enhanced image utilities for CUR8tr with robust placeholder generation
"""

import base64
import hashlib
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def create_modern_placeholder(title, size=(400, 300), style='gradient'):
    """
    Create a beautiful modern placeholder image as base64 data URL
    
    Args:
        title: Text to display on the placeholder
        size: Tuple of (width, height)
        style: 'gradient', 'solid', or 'pattern'
    
    Returns:
        Base64 data URL string
    """
    # Generate consistent color based on title
    title_hash = hashlib.md5(title.encode()).hexdigest()
    hue = int(title_hash[:2], 16)
    
    # Modern color palette
    color_schemes = [
        ('#667eea', '#764ba2'),  # Purple gradient
        ('#f093fb', '#f5576c'),  # Pink to red
        ('#4facfe', '#00f2fe'),  # Blue gradient
        ('#43e97b', '#38f9d7'),  # Green gradient
        ('#fa709a', '#fee140'),  # Pink to yellow
        ('#a8edea', '#fed6e3'),  # Mint to pink
    ]
    
    primary, secondary = color_schemes[hue % len(color_schemes)]
    
    # Create image
    img = Image.new('RGB', size, color=primary)
    draw = ImageDraw.Draw(img)
    
    # Create gradient background
    if style == 'gradient':
        for y in range(size[1]):
            # Linear gradient from primary to secondary
            ratio = y / size[1]
            r1, g1, b1 = tuple(int(primary[i:i+2], 16) for i in (1, 3, 5))
            r2, g2, b2 = tuple(int(secondary[i:i+2], 16) for i in (1, 3, 5))
            
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            
            draw.line([(0, y), (size[0], y)], fill=(r, g, b))
    
    # Try to use modern fonts
    try:
        font_large = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf', 32)
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', 16)
    except:
        try:
            font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 32)
            font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
    
    # Smart text wrapping
    words = title.split()
    lines = []
    current_line = []
    max_width = size[0] - 80  # Padding
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font_large)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # Word is too long, truncate it
                lines.append(word[:15] + '...' if len(word) > 15 else word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Limit to 2 lines for clean appearance
    lines = lines[:2]
    
    # Calculate text positioning
    line_height = 45
    total_height = len(lines) * line_height
    start_y = (size[1] - total_height) // 2
    
    # Draw text with modern styling
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_large)
        text_width = bbox[2] - bbox[0]
        x = (size[0] - text_width) // 2
        y = start_y + i * line_height
        
        # Modern shadow effect
        shadow_offset = 3
        draw.text((x + shadow_offset, y + shadow_offset), line, fill=(0, 0, 0, 80), font=font_large)
        
        # Main text in white
        draw.text((x, y), line, fill='white', font=font_large)
    
    # Add subtle CUR8tr branding
    brand_text = "CUR8tr"
    bbox = draw.textbbox((0, 0), brand_text, font=font_small)
    brand_width = bbox[2] - bbox[0]
    draw.text((size[0] - brand_width - 20, size[1] - 35), brand_text, fill=(255, 255, 255, 160), font=font_small)
    
    # Convert to base64 data URL
    buffer = BytesIO()
    img.save(buffer, format='PNG', quality=95, optimize=True)
    img_data = buffer.getvalue()
    base64_data = base64.b64encode(img_data).decode('utf-8')
    
    return f"data:image/png;base64,{base64_data}"

def validate_image_data_url(data_url):
    """
    Validate that a data URL contains valid image data
    
    Args:
        data_url: The data URL to validate
        
    Returns:
        Boolean indicating if the data URL is valid
    """
    if not data_url or not data_url.startswith('data:image/'):
        return False
    
    try:
        # Extract base64 data
        if ';base64,' not in data_url:
            return False
        
        header, base64_data = data_url.split(';base64,', 1)
        
        # Try to decode base64
        img_data = base64.b64decode(base64_data)
        
        # Try to open as image
        img = Image.open(BytesIO(img_data))
        img.verify()  # Verify it's a valid image
        
        return True
    except Exception:
        return False

def get_safe_image_url(image_field, fallback_title="Image", size=(400, 300)):
    """
    Get a safe image URL with automatic fallback to placeholder
    
    Args:
        image_field: The image field from database (could be data URL or file path)
        fallback_title: Title to use for placeholder if image is missing
        size: Size for placeholder image
        
    Returns:
        Valid data URL (either original or placeholder)
    """
    # If no image field, create placeholder
    if not image_field:
        return create_modern_placeholder(fallback_title, size)
    
    # If it's already a valid data URL, return it
    if validate_image_data_url(image_field):
        return image_field
    
    # Otherwise, create a placeholder
    return create_modern_placeholder(fallback_title, size)
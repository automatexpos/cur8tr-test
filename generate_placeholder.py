#!/usr/bin/env python3
"""
Utility to generate placeholder images for missing recommendation images.
This can be run to create missing image files when the database has image references
but the actual files don't exist.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import hashlib

def create_placeholder_image(filename, title, size=(400, 300)):
    """Create a placeholder image with title text"""
    # Create a simple gradient background based on title hash
    title_hash = hashlib.md5(title.encode()).hexdigest()
    hue = int(title_hash[:2], 16)
    
    # Create gradient colors
    if hue < 85:
        bg_color = '#4A90E2'  # Blue
    elif hue < 170:
        bg_color = '#2ECC71'  # Green
    else:
        bg_color = '#E74C3C'  # Red
    
    # Create image
    img = Image.new('RGB', size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to load a nice font
    try:
        font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Split title into lines if too long
    words = title.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font_large)
        if bbox[2] - bbox[0] < size[0] - 40:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                lines.append(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Limit to 3 lines
    lines = lines[:3]
    
    # Calculate total text height
    total_height = len(lines) * 30
    start_y = (size[1] - total_height) // 2
    
    # Draw text lines
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_large)
        text_width = bbox[2] - bbox[0]
        x = (size[0] - text_width) // 2
        y = start_y + i * 30
        
        # Draw text shadow
        draw.text((x + 2, y + 2), line, fill='rgba(0,0,0,0.3)', font=font_large)
        # Draw main text
        draw.text((x, y), line, fill='white', font=font_large)
    
    # Add a small watermark
    watermark = "CUR8tr"
    bbox = draw.textbbox((0, 0), watermark, font=font_small)
    w_width = bbox[2] - bbox[0]
    draw.text((size[0] - w_width - 10, size[1] - 25), watermark, fill='rgba(255,255,255,0.5)', font=font_small)
    
    return img

def main():
    """Generate missing placeholder images based on database records"""
    from app import app, db
    from models import Recommendation
    
    with app.app_context():
        recommendations = Recommendation.query.filter(Recommendation.image.isnot(None)).all()
        
        created_count = 0
        for rec in recommendations:
            if rec.image:
                # Extract filename from path
                filename = rec.image.split('/')[-1]
                filepath = os.path.join('static/uploads', filename)
                
                if not os.path.exists(filepath):
                    print(f"Creating placeholder for: {rec.title}")
                    
                    # Ensure uploads directory exists
                    os.makedirs('static/uploads', exist_ok=True)
                    
                    # Create placeholder image
                    img = create_placeholder_image(filename, rec.title)
                    img.save(filepath, 'JPEG', quality=85)
                    created_count += 1
                    print(f"  → Created: {filepath}")
        
        print(f"\nCreated {created_count} placeholder images")

if __name__ == '__main__':
    main()
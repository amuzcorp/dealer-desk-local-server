import os
from PIL import Image, ImageDraw, ImageFont

def create_app_icon():
    """Create default app icon"""
    if os.path.exists('app_icon.png'):
        print("App icon already exists.")
        return
    
    try:
        # Create 512x512 PNG image
        size = (512, 512)
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw background circle
        center = (size[0] // 2, size[1] // 2)
        radius = min(size) // 2 - 10
        bbox = (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius)
        draw.ellipse(bbox, fill=(0, 120, 212))
        
        # Draw text
        try:
            # Use system installed font
            font = ImageFont.truetype("arial.ttf", size=150)
        except IOError:
            # Use default font if font not found
            font = ImageFont.load_default()
        
        text = "DD"
        text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else font.getsize(text)
        text_position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2 - 20)
        
        # Add outline effect to text
        for offset_x, offset_y in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
            draw.text((text_position[0] + offset_x, text_position[1] + offset_y), text, font=font, fill=(0, 0, 0, 128))
        
        # Draw actual text
        draw.text(text_position, text, font=font, fill=(255, 255, 255))
        
        # Save image
        image.save('app_icon.png')
        print("App icon has been created.")
    except Exception as e:
        print(f"Error creating app icon: {e}")

if __name__ == "__main__":
    create_app_icon() 
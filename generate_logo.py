
from PIL import Image, ImageDraw, ImageFont
import os

def create_logo(text="Redit.io", output_path="reddit_io_logo_gen.png"):
    # Image size - wide enough for text
    width = 400
    height = 100
    
    # Create transparent image (RGBA)
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Try to load a nice font, fallback to default
    try:
        # MacOS usually has Arial or Helvetica
        font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if not os.path.exists(font_path):
             font_path = "/System/Library/Fonts/Helvetica.ttc"
        if not os.path.exists(font_path):
             # Try a different common path
             font_path = "/Library/Fonts/Arial.ttf"
             
        font = ImageFont.truetype(font_path, 60)
    except Exception as e:
        print(f"Could not load custom font: {e}, using default")
        font = ImageFont.load_default()
        
    # Text color: Red #FF4D4F (RedInk primary color-ish)
    text_color = (255, 77, 79, 255) 
    
    # Calculate text position to center it vertically
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw text
    draw.text((x, y), text, font=font, fill=text_color)
    
    # Save
    image.save(output_path, "PNG")
    print(f"Logo saved to {output_path}")

if __name__ == "__main__":
    create_logo()

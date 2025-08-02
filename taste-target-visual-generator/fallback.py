from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import textwrap
import os


def generate_image_pil_fallback(
    persona_name: str,
    brand_values: str,
    product_description: str,
    style_preference: str,
    image_type: str,
) -> Image.Image:
    """
    Generate a fallback image using PIL when AI generation is not available.
    Creates a styled poster with persona information.
    """
    
    # Create a new image with appropriate size based on type
    if image_type == "logo":
        width, height = 512, 512
        bg_color = (245, 245, 245)  # Light gray background for logos
    else:
        width, height = 1024, 1024
        bg_color = (20, 20, 20)  # Dark background for marketing materials
    
    # Create base image
    image = Image.new("RGBA", (width, height), bg_color)
    
    # Create a gradient overlay for visual interest
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # Add gradient effect
    for i in range(height):
        alpha = int(255 * (i / height) * 0.3)  # 30% max opacity
        draw_overlay.rectangle([(0, i), (width, i+1)], fill=(0, 0, 0, alpha))
    
    image = Image.alpha_composite(image.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(image)

    # Load fonts with fallback
    try:
        # Try common font paths
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "C:\\Windows\\Fonts\\Arial.ttf",  # Windows
        ]
        
        font_loaded = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                title_font = ImageFont.truetype(font_path, 48 if image_type != "logo" else 36)
                body_font = ImageFont.truetype(font_path, 28 if image_type != "logo" else 20)
                tag_font = ImageFont.truetype(font_path, 24 if image_type != "logo" else 18)
                font_loaded = True
                break
        
        if not font_loaded:
            raise Exception("No fonts found")
            
    except:
        # Fallback to default font
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        tag_font = ImageFont.load_default()

    padding = 50 if image_type != "logo" else 30
    y = padding

    # Colors based on style preference
    color_schemes = {
        "minimalist clean": {"primary": (255, 255, 255), "accent": (200, 200, 200)},
        "bold vibrant": {"primary": (255, 255, 255), "accent": (255, 100, 100)},
        "luxury premium": {"primary": (255, 215, 0), "accent": (200, 170, 0)},
        "natural organic": {"primary": (255, 255, 255), "accent": (150, 200, 150)},
        "tech futuristic": {"primary": (0, 255, 255), "accent": (0, 200, 200)},
        "artistic creative": {"primary": (255, 255, 255), "accent": (200, 150, 255)},
    }
    
    colors = color_schemes.get(style_preference, {"primary": (255, 255, 255), "accent": (200, 200, 200)})

    if image_type == "logo":
        # Center everything for logo
        # Draw a circle or shape in the center
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 3
        
        # Draw background circle
        draw.ellipse(
            [(center_x - radius, center_y - radius), 
             (center_x + radius, center_y + radius)],
            fill=colors["accent"]
        )
        
        # Draw product name in center
        text_bbox = draw.textbbox((0, 0), product_description, font=title_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        draw.text(
            (center_x - text_width // 2, center_y - text_height // 2),
            product_description,
            font=title_font,
            fill=colors["primary"]
        )
        
        # Add tagline below
        tagline = f"For {persona_name}"
        text_bbox = draw.textbbox((0, 0), tagline, font=tag_font)
        text_width = text_bbox[2] - text_bbox[0]
        draw.text(
            (center_x - text_width // 2, center_y + radius + 20),
            tagline,
            font=tag_font,
            fill=colors["primary"]
        )
    else:
        # Marketing poster layout
        # Draw Persona Name (Title)
        draw.text((padding, y), persona_name, font=title_font, fill=colors["primary"])
        text_bbox = draw.textbbox((padding, y), persona_name, font=title_font)
        y += (text_bbox[3] - text_bbox[1]) + 30

        # Draw Brand Values as stylized tags
        tag_margin = 10
        tag_padding = 12
        tag_height = 40
        tags = [tag.strip() for tag in brand_values.split(",")]

        x = padding
        for tag in tags:
            text_bbox = draw.textbbox((0, 0), tag, font=tag_font)
            tag_width = text_bbox[2] - text_bbox[0]
            tag_box = [x, y, x + tag_width + tag_padding * 2, y + tag_height]
            
            # Draw tag background
            draw.rectangle(tag_box, fill=(*colors["accent"], 50), outline=colors["accent"])
            draw.text((x + tag_padding, y + 8), tag, font=tag_font, fill=colors["primary"])
            x = tag_box[2] + tag_margin
            
            # Wrap to next line if needed
            if x > width - padding - 100:
                x = padding
                y += tag_height + tag_margin

        y += tag_height + 30

        # Draw product description, wrapped
        max_chars = 60 if width > 800 else 40
        wrapped_description = textwrap.fill(product_description, width=max_chars)
        draw.multiline_text((padding, y), wrapped_description, font=body_font, fill=colors["primary"])

        # Add footer text (style + type)
        footer = f"Style: {style_preference} | Type: {image_type}"
        text_bbox = draw.textbbox((0, 0), footer, font=body_font)
        footer_height = text_bbox[3] - text_bbox[1]
        draw.text(
            (padding, height - padding - footer_height),
            footer,
            font=body_font,
            fill=colors["accent"]
        )

    return image.convert("RGB")
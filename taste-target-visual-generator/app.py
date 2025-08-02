import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import math
import traceback
import os
from huggingface_hub import InferenceClient
from io import BytesIO
import base64

# Initialize Hugging Face client with better error handling
HF_TOKEN = os.getenv("HUGGINGFACE_API_KEY")
HF_AVAILABLE = False
hf_client = None

print("=" * 50)
print("🚀 TasteTarget Visual Generator Starting...")
print("=" * 50)

if HF_TOKEN:
    try:
        hf_client = InferenceClient(token=HF_TOKEN)
        HF_AVAILABLE = True
        print("✅ Hugging Face API configured successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize Hugging Face client: {e}")
        HF_AVAILABLE = False
else:
    print("⚠️  No Hugging Face API key found in environment variables.")
    print("💡 Add HUGGINGFACE_API_KEY as a Space secret for AI-powered generation.")
    HF_AVAILABLE = False

print(f"🤖 AI Generation Available: {HF_AVAILABLE}")
print("=" * 50)

def generate_image_with_huggingface(persona_name, brand_values, product_description, style_preference, image_type):
    """Generate high-quality marketing images using Hugging Face"""
    
    if not HF_AVAILABLE or not hf_client:
        print("⚠️  HF client not available, skipping AI generation")
        return None
    
    print(f"🤖 Starting AI generation for: {product_description}")
    
    # Style mapping for prompts
    style_prompts = {
        "minimalist clean": "minimalist, clean design, white space, modern, simple, elegant",
        "bold vibrant": "bold colors, vibrant, dynamic, energetic, eye-catching, colorful",
        "luxury premium": "luxury, premium, elegant, sophisticated, gold accents, high-end",
        "natural organic": "natural, organic, earth tones, eco-friendly, sustainable, green",
        "tech futuristic": "futuristic, technology, neon, digital, innovative, cyber",
        "artistic creative": "artistic, creative, abstract, unique, expressive, imaginative"
    }
    
    # Build the prompt
    style_desc = style_prompts.get(style_preference, "modern, professional")
    
    if image_type == "logo":
        prompt = f"""Professional logo design for {product_description}.
        Style: {style_desc}
        Brand values: {brand_values}
        Minimalist logo, vector style, clean design, memorable, professional branding.
        High quality, centered composition, suitable for business use."""
    else:
        prompt = f"""Professional marketing poster for {product_description}.
        Target audience: {persona_name}
        Visual style: {style_desc}
        Brand values: {brand_values}
        
        Marketing advertisement, commercial quality, professional design.
        Eye-catching composition, modern layout, compelling visuals.
        Include subtle design elements that appeal to the target demographic."""
    
    negative_prompt = "low quality, amateur, blurry, distorted, ugly, bad anatomy, bad composition, pixelated, watermark, text overlay"
    
    # Try different models in order of preference
    models_to_try = [
        {
            "name": "black-forest-labs/FLUX.1-schnell",
            "params": {
                "width": 1024 if image_type == "marketing" else 512,
                "height": 1024 if image_type == "marketing" else 512
            }
        },
        {
            "name": "stabilityai/stable-diffusion-xl-base-1.0",
            "params": {
                "negative_prompt": negative_prompt,
                "guidance_scale": 7.5,
                "num_inference_steps": 25,
                "width": 1024 if image_type == "marketing" else 512,
                "height": 1024 if image_type == "marketing" else 512
            }
        },
        {
            "name": "runwayml/stable-diffusion-v1-5",
            "params": {
                "negative_prompt": negative_prompt,
                "guidance_scale": 7.5,
                "num_inference_steps": 20,
                "width": 512,
                "height": 512
            }
        }
    ]
    
    for model_config in models_to_try:
        model_name = model_config["name"]
        model_params = model_config["params"]
        
        try:
            print(f"🎨 Trying model: {model_name}")
            
            # Generate image
            image = hf_client.text_to_image(
                prompt,
                model=model_name,
                **model_params
            )
            
            print(f"✅ Successfully generated image with {model_name}")
            return image
            
        except Exception as e:
            print(f"❌ Model {model_name} failed: {str(e)}")
            continue
    
    print("❌ All AI models failed")
    return None

def generate_image_pil_fallback(persona_name, brand_values, product_description, style_preference, image_type):
    """Enhanced PIL-based image generation as fallback"""
    try:
        print(f"🎨 Generating {image_type} with PIL fallback - Style: {style_preference}")
        
        width, height = 512, 512
        
        # Enhanced color schemes
        styles = {
            "minimalist clean": {"bg": (250, 250, 250), "fg": (50, 50, 50), "accent": (120, 120, 120)},
            "bold vibrant": {"bg": (255, 20, 147), "fg": (255, 255, 255), "accent": (0, 255, 255)},
            "luxury premium": {"bg": (20, 20, 20), "fg": (218, 165, 32), "accent": (255, 215, 0)},
            "natural organic": {"bg": (245, 245, 220), "fg": (34, 139, 34), "accent": (107, 142, 35)},
            "tech futuristic": {"bg": (10, 10, 50), "fg": (0, 255, 255), "accent": (138, 43, 226)},
            "artistic creative": {"bg": (255, 245, 238), "fg": (255, 69, 0), "accent": (255, 140, 0)}
        }
        
        style = styles.get(style_preference, styles["minimalist clean"])
        
        img = Image.new('RGB', (width, height), style["bg"])
        draw = ImageDraw.Draw(img)
        
        # Enhanced font loading with more fallbacks
        font_large = None
        font_medium = None
        font_small = None
        
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "C:/Windows/Fonts/arial.ttf",  # Windows
        ]
        
        for path in font_paths:
            try:
                font_large = ImageFont.truetype(path, 42)
                font_medium = ImageFont.truetype(path, 24)
                font_small = ImageFont.truetype(path, 18)
                print(f"✅ Loaded font: {path}")
                break
            except:
                continue
        
        if not font_large:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
            print("⚠️  Using default font")
        
        if image_type == "logo":
            # Enhanced logo generation
            words = product_description.strip().split()
            initials = ''.join([w[0].upper() for w in words[:2]]) if words else "TT"
            
            center_x, center_y = 256, 256
            
            # Create sophisticated logo shapes based on style
            if style_preference == "minimalist clean":
                # Clean circles with subtle depth
                draw.ellipse([156, 156, 356, 356], outline=style["fg"], width=4)
                draw.ellipse([176, 176, 336, 336], outline=style["accent"], width=1)
                
            elif style_preference == "luxury premium":
                # Elegant diamond with inner details
                points = [(256, 146), (366, 256), (256, 366), (146, 256)]
                draw.polygon(points, outline=style["fg"], width=4)
                inner_points = [(256, 186), (316, 256), (256, 326), (196, 256)]
                draw.polygon(inner_points, outline=style["accent"], width=2)
                
            elif style_preference == "tech futuristic":
                # Sophisticated hexagon with tech elements
                hex_points = []
                for i in range(6):
                    angle = i * 60 * math.pi / 180
                    x = center_x + 90 * math.cos(angle)
                    y = center_y + 90 * math.sin(angle)
                    hex_points.append((x, y))
                draw.polygon(hex_points, outline=style["fg"], width=3)
                
                # Inner tech pattern
                for radius in [60, 40]:
                    inner_hex = []
                    for i in range(6):
                        angle = i * 60 * math.pi / 180
                        x = center_x + radius * math.cos(angle)
                        y = center_y + radius * math.sin(angle)
                        inner_hex.append((x, y))
                    draw.polygon(inner_hex, outline=style["accent"], width=1)
                
            elif style_preference == "natural organic":
                # Organic flowing design
                draw.ellipse([156, 156, 356, 356], outline=style["fg"], width=4)
                # Leaf-like elements
                draw.arc([176, 186, 256, 236], 45, 225, fill=style["accent"], width=3)
                draw.arc([256, 276, 336, 326], 225, 45, fill=style["accent"], width=3)
                
            elif style_preference == "bold vibrant":
                # Dynamic geometric shapes
                draw.rectangle([156, 156, 356, 356], outline=style["fg"], width=5)
                draw.rectangle([176, 176, 336, 336], outline=style["accent"], width=3)
                draw.ellipse([196, 196, 316, 316], outline=style["fg"], width=2)
                
            else:  # artistic creative
                # Creative abstract design
                import random
                random.seed(hash(product_description))  # Consistent randomness
                
                for i in range(12):
                    x1 = random.randint(156, 256)
                    y1 = random.randint(156, 256)
                    x2 = random.randint(256, 356)
                    y2 = random.randint(256, 356)
                    draw.arc([x1, y1, x2, y2], 0, 180, fill=style["accent"], width=2)
                
                draw.ellipse([196, 196, 316, 316], outline=style["fg"], width=3)
            
            # Draw initials with better positioning
            bbox = draw.textbbox((0, 0), initials, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            draw.text((x, y), initials, fill=style["fg"], font=font_large)
            
            # Add product name with better formatting
            product_text = product_description[:30]
            if len(product_description) > 30:
                product_text += "..."
            
            bbox = draw.textbbox((0, 0), product_text, font=font_small)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, 430), product_text, fill=style["fg"], font=font_small)
                
        else:  # marketing visual
            # Enhanced marketing visual generation
            if style_preference == "minimalist clean":
                draw.ellipse([126, 126, 386, 386], outline=style["fg"], width=3)
                draw.line([(256, 146), (256, 366)], fill=style["accent"], width=1)
                draw.line([(146, 256), (366, 256)], fill=style["accent"], width=1)
                
            elif style_preference == "bold vibrant":
                for i in range(7):
                    offset = i * 12
                    draw.rectangle([126+offset, 126+offset, 386-offset, 386-offset], 
                                 outline=style["fg"], width=2)
                    
            elif style_preference == "luxury premium":
                # Elegant frame with corner details
                draw.rectangle([126, 126, 386, 386], outline=style["fg"], width=4)
                draw.rectangle([146, 146, 366, 366], outline=style["accent"], width=1)
                # Corner decorations
                corner_size = 15
                for corner in [(146, 146), (366-corner_size, 146), (146, 366-corner_size), (366-corner_size, 366-corner_size)]:
                    draw.rectangle([corner[0]-5, corner[1]-5, corner[0]+corner_size, corner[1]+corner_size], 
                                 outline=style["accent"], width=2)
                
            elif style_preference == "natural organic":
                # Organic wave patterns
                for i in range(12):
                    y = 146 + i * 18
                    points = []
                    for x in range(146, 366, 8):
                        wave_y = y + 8 * math.sin((x - 146) * 0.05 + i * 0.3)
                        points.extend([x, wave_y])
                    if len(points) >= 4:
                        draw.line(points, fill=style["accent"], width=1)
                
            elif style_preference == "tech futuristic":
                # Sophisticated grid with highlights
                grid_size = 25
                for i in range(146, 366, grid_size):
                    draw.line([(i, 146), (i, 366)], fill=style["accent"], width=1)
                    draw.line([(146, i), (366, i)], fill=style["accent"], width=1)
                
                # Highlight intersections
                for x in range(146, 366, grid_size*2):
                    for y in range(146, 366, grid_size*2):
                        draw.ellipse([x-3, y-3, x+3, y+3], fill=style["fg"])
                
            else:  # artistic creative
                # Creative spiral pattern
                center_x, center_y = 256, 256
                for angle in range(0, 360, 8):
                    rad = math.radians(angle)
                    radius = 30 + angle * 0.2
                    x = center_x + radius * math.cos(rad)
                    y = center_y + radius * math.sin(rad)
                    if 146 <= x <= 366 and 146 <= y <= 366:
                        size = 2 + (angle % 40) // 10
                        draw.ellipse([x-size, y-size, x+size, y+size], fill=style["accent"])
            
            # Add text with better styling
            # Persona name
            bbox = draw.textbbox((0, 0), persona_name, font=font_medium)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, 410), persona_name, fill=style["fg"], font=font_medium)
            
            # Product description
            product_text = product_description[:35]
            if len(product_description) > 35:
                product_text += "..."
                
            bbox = draw.textbbox((0, 0), product_text, font=font_small)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, 440), product_text, fill=style["accent"], font=font_small)
            
            # Brand values
            values_text = f"Values: {brand_values[:25]}"
            if len(brand_values) > 25:
                values_text += "..."
            
            bbox = draw.textbbox((0, 0), values_text, font=font_small)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, 465), values_text, fill=style["accent"], font=font_small)
        
        print(f"✅ Successfully generated {image_type} using PIL")
        return img
        
    except Exception as e:
        print(f"❌ Error in PIL fallback: {str(e)}")
        print(traceback.format_exc())
        
        # Create simple error image
        img = Image.new('RGB', (512, 512), (255, 200, 200))
        draw = ImageDraw.Draw(img)
        
        error_msg = "Generation Error"
        font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), error_msg, font=font)
        text_width = bbox[2] - bbox[0]
        x = (512 - text_width) // 2
        draw.text((x, 240), error_msg, fill=(255, 0, 0), font=font)
        draw.text((x, 260), "Please try again", fill=(255, 0, 0), font=font)
        
        return img

def generate_image(persona_name, brand_values, product_description, style_preference, image_type, use_ai=True):
    """Main function that tries HF first, then falls back to PIL"""
    
    print("=" * 40)
    print(f"🚀 Generation Request:")
    print(f"   👤 Persona: {persona_name}")
    print(f"   📦 Product: {product_description}")
    print(f"   🎨 Style: {style_preference}")
    print(f"   📸 Type: {image_type}")
    print(f"   🤖 Use AI: {use_ai}")
    print(f"   ✅ HF Available: {HF_AVAILABLE}")
    print("=" * 40)
    
    # Try Hugging Face generation first if available and requested
    if use_ai and HF_AVAILABLE:
        try:
            print("🤖 Attempting Hugging Face AI generation...")
            hf_image = generate_image_with_huggingface(
                persona_name, brand_values, product_description, 
                style_preference, image_type
            )
            if hf_image:
                print("✅ AI generation successful!")
                return hf_image
            else:
                print("⚠️  AI generation returned None, using fallback")
        except Exception as e:
            print(f"❌ AI generation failed: {str(e)}")
            print("🔄 Falling back to PIL generation...")
    else:
        if not use_ai:
            print("🎨 AI generation disabled by user")
        else:
            print("⚠️  AI not available, using PIL fallback")
    
    # Fall back to PIL-based generation
    result = generate_image_pil_fallback(
        persona_name, brand_values, product_description, 
        style_preference, image_type
    )
    
    print("✅ Generation completed!")
    print("=" * 40)
    return result

# Create the Gradio interface with better configuration
iface = gr.Interface(
    fn=generate_image,
    inputs=[
        gr.Textbox(
            label="👤 Persona Name", 
            value="The Conscious Pioneer",
            placeholder="e.g., The Tech Enthusiast, The Eco Warrior"
        ),
        gr.Textbox(
            label="💎 Brand Values", 
            value="sustainability, ethical, quality",
            placeholder="e.g., innovation, trust, premium, sustainable"
        ),
        gr.Textbox(
            label="📦 Product/Brand Name", 
            value="EcoStep Footwear",
            placeholder="e.g., TechFit Pro, Green Living Co"
        ),
        gr.Dropdown(
            label="🎨 Visual Style",
            choices=["minimalist clean", "bold vibrant", "luxury premium", 
                     "natural organic", "tech futuristic", "artistic creative"],
            value="minimalist clean",
            info="Choose the visual aesthetic for your brand"
        ),
        gr.Radio(
            label="📸 Output Type", 
            choices=["marketing", "logo"], 
            value="logo",
            info="Logo for branding, Marketing for promotional visuals"
        ),
        gr.Checkbox(
            label="🤖 Use AI Generation", 
            value=True, 
            visible=HF_AVAILABLE,
            info="Use advanced AI models for higher quality results"
        )
    ],
    outputs=gr.Image(
        type="pil", 
        label="Generated Visual",
        show_label=True
    ),
    title="🎨 TasteTarget Visual Generator",
    description=f"""
    **Generate professional marketing visuals and logos tailored to your target audience personas.**
    
    {'✨ **AI-powered generation is active!** High-quality results using advanced diffusion models.' if HF_AVAILABLE else '⚠️  **Using enhanced PIL generation.** Add `HUGGINGFACE_API_KEY` as a Space secret for AI features.'}
    
    ### How to use:
    1. **Enter your target persona** (e.g., "The Tech-Savvy Professional")
    2. **Specify brand values** (comma-separated, e.g., "innovation, trust, quality")  
    3. **Enter your product/brand name**
    4. **Choose a visual style** that matches your brand aesthetic
    5. **Select output type** - Logo for branding, Marketing for promotional content
    6. **Click Submit** to generate your visual!
    
    ### Tips:
    - Be specific with persona names for better targeting
    - Use 3-5 brand values for best results
    - Try different styles to find your perfect aesthetic
    """,
    examples=[
        ["The Conscious Pioneer", "sustainability, ethical, innovation", "EcoStep Footwear", "natural organic", "logo", True],
        ["The Digital Explorer", "innovation, technology, speed", "TechFit Pro", "tech futuristic", "logo", True],
        ["The Luxury Connoisseur", "premium, exclusive, craftsmanship", "Luxe Collection", "luxury premium", "logo", True],
        ["The Creative Rebel", "artistic, unique, bold", "ArtWear Studio", "artistic creative", "marketing", True],
        ["The Minimalist", "simplicity, clean, modern", "Pure Design Co", "minimalist clean", "marketing", True],
        ["The Bold Trendsetter", "vibrant, energetic, dynamic", "Neon Lifestyle", "bold vibrant", "marketing", True],
    ],
    theme=gr.themes.Soft(),
    flagging_mode="never",  # Updated from deprecated allow_flagging
    cache_examples=True,
    api_name="predict"  # This creates the /predict endpoint for API access
)

if __name__ == "__main__":
    print("\n" + "🚀 " + "="*48 + " 🚀")
    print("    🎨 TasteTarget Visual Generator Ready!")
    print("🚀 " + "="*48 + " 🚀\n")
    
    if HF_AVAILABLE:
        print("✅ AI Generation: ENABLED")
    else:
        print("⚠️  AI Generation: DISABLED")
        print("💡 To enable AI: Add HUGGINGFACE_API_KEY as a Space secret")
    
    print(f"🌐 Launching interface...")
    print("="*52)
    
    iface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        share=False,
        show_api=True  # This shows the API documentation
    )
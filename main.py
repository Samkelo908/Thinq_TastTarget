from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import json
import httpx
from datetime import datetime
import logging
import asyncio
from openai import OpenAI
import base64
from gradio_client import Client
import time
import math

# Load environment variables
load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QLOO_API_KEY = os.getenv("QLOO_API_KEY")
QLOO_API_URL = os.getenv("QLOO_API_URL", "https://hackathon.api.qloo.com")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configure logging
log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TasteTarget API - Qloo + OpenAI",
    description="AI-Powered Cultural Targeting using Qloo's Taste AI and OpenAI GPT-4",
    version="3.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ProductInput(BaseModel):
    product_name: str = Field(..., example="Eco-Friendly Vegan Sneakers")
    product_description: str = Field(..., example="Minimalist design, sustainable materials, zero waste production")
    brand_values: List[str] = Field(default=[], example=["sustainability", "minimalism", "ethical"])
    target_mood: List[str] = Field(default=[], example=["conscious", "modern", "clean"])
    campaign_tone: str = Field(default="balanced", example="balanced")

class TastePersona(BaseModel):
    persona_id: str
    name: str
    description: str
    cultural_interests: Dict[str, List[str]]
    psychographics: List[str]
    preferred_channels: List[str]
    influencer_types: List[str]
    specific_influencers: Optional[Dict[str, List[str]]] = Field(default_factory=dict)

class CampaignCopy(BaseModel):
    persona_id: str
    tagline: str
    social_caption: str
    ad_copy: str
    email_subject: str
    product_description: str

class VisualGenerationRequest(BaseModel):
    persona_name: str = Field(..., example="The Conscious Pioneer")
    brand_values: str = Field(..., example="sustainability, ethical, quality")
    product_description: str = Field(..., example="eco-friendly vegan sneakers")
    style_preference: str = Field(default="minimalist clean", example="natural organic")
    image_type: str = Field(default="marketing", example="marketing", description="Type of image: 'marketing' or 'logo'")

class TasteTargetResponse(BaseModel):
    product_name: str
    personas: List[TastePersona]
    campaign_copies: List[CampaignCopy]
    generation_timestamp: str
    suggestions: Dict[str, List[str]]
    data_source: str = Field(default="Qloo Taste AI + OpenAI GPT-4")
    visual_generation_endpoint: str = Field(default="https://huggingface.co/spaces/Samkelo28/taste-target-visual-generator")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    qloo_connected: bool
    openai_connected: bool

# OpenAI Integration
async def call_openai_api(prompt: str, temperature: float = 0.7, model: str = "gpt-4o-mini") -> str:
    """Call OpenAI API for text generation"""
    try:
        # Use the async approach with asyncio
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=model,
            messages=[
                {"role": "system", "content": "You are a marketing expert specializing in cultural intelligence and audience targeting. Always respond with valid JSON when asked."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

def extract_json_from_response(response: str) -> dict:
    """Extract JSON from OpenAI response"""
    try:
        # Clean response
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        # Find JSON in response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response[json_start:json_end]
            return json.loads(json_str)
        
        # Try to parse entire response as JSON
        return json.loads(response)
        
    except Exception as e:
        logger.warning(f"JSON parse error: {e}")
        logger.debug(f"Response was: {response}")
        return {}

# Qloo API Integration (same as before)
async def call_qloo_api(product_info: dict) -> List[dict]:
    """Call Qloo API v2 for taste-based insights"""
    if not QLOO_API_KEY:
        logger.warning("QLOO_API_KEY not found, using mock data")
        return await mock_qloo_api(product_info)
    
    headers = {
        "X-Api-Key": QLOO_API_KEY,
        "Content-Type": "application/json"
    }
    
    clusters = []
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            tag_mappings = {
                "sustainability": ["urn:tag:genre:lifestyle:eco-friendly", "urn:tag:genre:lifestyle:sustainable"],
                "innovation": ["urn:tag:genre:tech:innovative", "urn:tag:genre:lifestyle:modern"],
                "luxury": ["urn:tag:genre:lifestyle:luxury", "urn:tag:genre:lifestyle:premium"],
                "minimalism": ["urn:tag:genre:lifestyle:minimalist", "urn:tag:genre:lifestyle:simple"],
                "ethical": ["urn:tag:genre:lifestyle:ethical", "urn:tag:genre:lifestyle:conscious"],
                "quality": ["urn:tag:genre:lifestyle:quality", "urn:tag:genre:lifestyle:premium"]
            }
            
            # Query Qloo for insights based on brand values
            for i, value in enumerate(product_info.get('brand_values', [])[:3]):
                try:
                    tags = tag_mappings.get(value, [f"urn:tag:genre:lifestyle:{value}"])
                    
                    base_url = f"{QLOO_API_URL}/v2/insights"
                    params = {
                        "filter.type": "urn:demographics",
                        "signal.interests.tags": tags[0] if tags else f"urn:tag:genre:lifestyle:{value}"
                    }
                    
                    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                    url = f"{base_url}?{query_string}"
                    
                    logger.info(f"Calling Qloo API: {url}")
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        insights = response.json()
                        logger.info(f"Qloo insights received for {value}")
                        
                        cluster = convert_qloo_insights_to_cluster(insights, value, i)
                        if cluster:
                            clusters.append(cluster)
                    else:
                        logger.warning(f"Qloo API returned {response.status_code} for {value}")
                        
                except Exception as e:
                    logger.error(f"Error querying Qloo for {value}: {e}")
                    
    except Exception as e:
        logger.error(f"Qloo API error: {str(e)}")
    
    if clusters:
        logger.info(f"Successfully retrieved {len(clusters)} clusters from Qloo")
        return clusters
    else:
        logger.warning("No usable data from Qloo API, using mock data")
        return await mock_qloo_api(product_info)

def convert_qloo_insights_to_cluster(insights: dict, cluster_name: str, index: int) -> dict:
    """Convert Qloo API v2 insights response to our cluster format"""
    try:
        cluster = {
            "cluster_id": f"qloo_{cluster_name}_{index}",
            "interests": {
                "music": [],
                "reading": [],
                "dining": [],
                "travel": [],
                "fashion": []
            }
        }
        
        # Parse Qloo insights data
        if "data" in insights:
            data = insights["data"]
            
            if isinstance(data, list):
                for item in data[:10]:
                    if "category" in item and "name" in item:
                        category = item["category"].lower()
                        name = item["name"]
                        
                        # Map to our categories
                        if "music" in category or "artist" in category:
                            cluster["interests"]["music"].append(name)
                        elif "book" in category or "author" in category:
                            cluster["interests"]["reading"].append(name)
                        elif "restaurant" in category or "food" in category:
                            cluster["interests"]["dining"].append(name)
                        elif "destination" in category or "travel" in category:
                            cluster["interests"]["travel"].append(name)
                        elif "brand" in category or "fashion" in category:
                            cluster["interests"]["fashion"].append(name)
            
            # Ensure each category has at least some interests
            for category in cluster["interests"]:
                if not cluster["interests"][category]:
                    cluster["interests"][category] = get_default_interests(category, cluster_name)
        
        return cluster
        
    except Exception as e:
        logger.error(f"Error converting Qloo insights: {e}")
        return None

def get_default_interests(category: str, cluster_name: str) -> List[str]:
    """Get default interests for a category based on cluster name"""
    defaults = {
        "music": {
            "sustainability": ["indie folk", "acoustic", "world music"],
            "innovation": ["electronic", "experimental", "synth"],
            "luxury": ["jazz", "classical", "lounge"],
            "default": ["pop", "indie", "alternative"]
        },
        "reading": {
            "sustainability": ["eco blogs", "philosophy", "nature writing"],
            "innovation": ["tech blogs", "sci-fi", "futurism"],
            "luxury": ["art books", "biographies", "luxury magazines"],
            "default": ["bestsellers", "blogs", "magazines"]
        },
        "dining": {
            "sustainability": ["farm-to-table", "vegan", "organic"],
            "innovation": ["molecular gastronomy", "fusion", "pop-ups"],
            "luxury": ["fine dining", "michelin", "wine bars"],
            "default": ["cafes", "local cuisine", "brunch"]
        },
        "travel": {
            "sustainability": ["eco-lodges", "hiking", "nature"],
            "innovation": ["smart cities", "tech hubs", "urban"],
            "luxury": ["resorts", "exclusive destinations", "yachts"],
            "default": ["city breaks", "cultural sites", "weekend trips"]
        },
        "fashion": {
            "sustainability": ["sustainable brands", "vintage", "ethical"],
            "innovation": ["techwear", "smart fashion", "futuristic"],
            "luxury": ["designer", "couture", "bespoke"],
            "default": ["contemporary", "trendy", "seasonal"]
        }
    }
    
    return defaults.get(category, {}).get(cluster_name, defaults[category]["default"])[:5]

async def mock_qloo_api(product_info: dict) -> List[dict]:
    """Fallback mock data when Qloo API is unavailable"""
    await asyncio.sleep(0.5)
    
    clusters = []
    
    if "sustainability" in product_info.get("brand_values", []) or "ethical" in product_info.get("brand_values", []):
        clusters.append({
            "cluster_id": "eco_conscious",
            "interests": {
                "music": ["indie folk", "acoustic", "world music", "nature sounds", "ambient"],
                "reading": ["environmental books", "sustainable living blogs", "philosophy", "poetry", "mindfulness"],
                "dining": ["farm-to-table", "vegan restaurants", "organic cafes", "juice bars", "farmers markets"],
                "travel": ["eco-lodges", "national parks", "hiking trails", "sustainable tourism", "volunteer trips"],
                "fashion": ["sustainable brands", "vintage shops", "minimalist style", "natural fabrics", "ethical fashion"]
            }
        })
    
    if "innovation" in product_info.get("brand_values", []) or "modern" in product_info.get("brand_values", []):
        clusters.append({
            "cluster_id": "tech_innovator",
            "interests": {
                "music": ["electronic", "synthwave", "experimental", "techno", "future bass"],
                "reading": ["tech blogs", "sci-fi novels", "innovation magazines", "startup stories", "futurism"],
                "dining": ["trendy restaurants", "food tech", "molecular gastronomy", "pop-ups", "delivery apps"],
                "travel": ["smart cities", "tech hubs", "conferences", "urban exploration", "digital nomad spots"],
                "fashion": ["techwear", "designer collaborations", "smart accessories", "limited editions", "streetwear"]
            }
        })
    
    if len(clusters) < 3:
        clusters.append({
            "cluster_id": "balanced_modern",
            "interests": {
                "music": ["pop", "indie", "podcasts", "spotify playlists", "live music"],
                "reading": ["bestsellers", "online articles", "lifestyle blogs", "self-help", "newsletters"],
                "dining": ["trendy cafes", "brunch spots", "food delivery", "local favorites", "social dining"],
                "travel": ["weekend trips", "city breaks", "instagram spots", "airbnb", "group travel"],
                "fashion": ["contemporary brands", "online shopping", "seasonal trends", "athleisure", "accessories"]
            }
        })
    
    return clusters[:3]

# Persona Generation with OpenAI
async def generate_personas_with_openai(product_input: ProductInput, taste_clusters: List[dict]) -> List[TastePersona]:
    """Generate personas using OpenAI GPT-4"""
    personas = []
    
    for i, cluster in enumerate(taste_clusters):
        interests_summary = []
        for category, items in cluster['interests'].items():
            interests_summary.append(f"{category}: {', '.join(items[:3])}")
        
        prompt = f"""Create a detailed marketing persona for {product_input.product_name}.

Product: {product_input.product_description}
Brand values: {', '.join(product_input.brand_values)}
Cultural interests from data: {'; '.join(interests_summary)}

Generate a JSON object with exactly these fields:
{{
  "persona_name": "Creative 2-3 word name that captures their essence",
  "description": "2-3 sentence description of who they are and what drives them",
  "psychographics": ["trait1", "trait2", "trait3", "trait4", "trait5"],
  "preferred_channels": ["channel1", "channel2", "channel3", "channel4"],
  "influencer_types": ["type1", "type2", "type3"],
  "specific_influencers": {{
    "musicians": ["Real artist name 1", "Real artist name 2", "Real artist name 3"],
    "lifestyle_bloggers": ["Real blogger/creator name 1", "Real blogger name 2", "Real blogger name 3"],
    "thought_leaders": ["Real thought leader 1", "Real thought leader 2", "Real thought leader 3"]
  }}
}}

Based on the cultural interests, suggest REAL, CURRENT influencers who are active in 2024/2025. 
For musicians, include artists from the music genres mentioned in the interests.
For lifestyle bloggers, include real Instagram/TikTok/YouTube creators who align with these interests.
For thought leaders, include real industry experts, authors, or speakers relevant to the brand values.

Important: Return ONLY the JSON object, no other text or markdown."""

        try:
            response = await call_openai_api(prompt, temperature=0.7)
            persona_data = extract_json_from_response(response)
            
            if persona_data and "persona_name" in persona_data:
                # Extract specific influencers if provided, otherwise use empty dict
                specific_influencers = persona_data.get('specific_influencers', {})
                
                personas.append(TastePersona(
                    persona_id=cluster['cluster_id'],
                    name=persona_data.get('persona_name', f'Persona {i+1}'),
                    description=persona_data.get('description', 'A key customer segment'),
                    cultural_interests=cluster['interests'],
                    psychographics=persona_data.get('psychographics', ['innovative', 'conscious', 'modern']),
                    preferred_channels=persona_data.get('preferred_channels', ['Instagram', 'Email', 'YouTube']),
                    influencer_types=persona_data.get('influencer_types', ['Micro-influencers', 'Experts']),
                    specific_influencers=specific_influencers
                ))
                logger.info(f"Successfully generated persona: {persona_data.get('persona_name')}")
            else:
                raise ValueError("Invalid persona data from OpenAI")
                
        except Exception as e:
            logger.error(f"Persona generation error: {e}")
            personas.append(create_fallback_persona(cluster, i))
    
    return personas

def create_fallback_persona(cluster: dict, index: int) -> TastePersona:
    """Fallback persona when generation fails"""
    names = {
        "eco_conscious": "The Conscious Pioneer",
        "tech_innovator": "The Digital Explorer",
        "premium_lifestyle": "The Luxury Connoisseur",
        "balanced_modern": "The Modern Optimizer"
    }
    
    return TastePersona(
        persona_id=cluster['cluster_id'],
        name=names.get(cluster['cluster_id'], f"Persona {index + 1}"),
        description="A discerning customer who values quality and authenticity in their choices.",
        cultural_interests=cluster['interests'],
        psychographics=["thoughtful", "quality-focused", "authentic", "curious", "trendsetting"],
        preferred_channels=["Instagram", "Newsletter", "YouTube", "LinkedIn"],
        influencer_types=["Industry experts", "Lifestyle creators", "Thought leaders"],
        specific_influencers={}
    )

async def generate_campaign_copy_with_openai(product_input: ProductInput, personas: List[TastePersona]) -> List[CampaignCopy]:
    """Generate campaign copy using OpenAI"""
    copies = []
    
    tone_guide = {
        "minimal": "Use few words, be direct and impactful",
        "balanced": "Professional yet approachable tone",
        "expressive": "Creative and emotionally engaging",
        "bold": "Strong statements and confident messaging"
    }
    
    for persona in personas:
        prompt = f"""Create marketing copy for {product_input.product_name} targeting {persona.name}.

Product: {product_input.product_description}
Customer Profile: {persona.description}
Their interests include: {', '.join(persona.cultural_interests.get('music', [])[:2])} music, {', '.join(persona.cultural_interests.get('fashion', [])[:2])} fashion
Tone: {product_input.campaign_tone} - {tone_guide.get(product_input.campaign_tone, 'balanced')}

Generate a JSON object with exactly these fields:
{{
  "tagline": "Maximum 8 words, memorable and impactful",
  "social_caption": "2-3 sentences for Instagram/TikTok with relevant emojis that speak to their interests",
  "ad_copy": "3-4 compelling sentences for display advertising",
  "email_subject": "Under 50 characters, creates curiosity",
  "product_description": "2-3 benefit-focused sentences tailored to this persona"
}}

Important: Return ONLY the JSON object, no other text or markdown."""

        try:
            response = await call_openai_api(prompt, temperature=0.8)
            copy_data = extract_json_from_response(response)
            
            if copy_data and "tagline" in copy_data:
                copies.append(CampaignCopy(
                    persona_id=persona.persona_id,
                    tagline=copy_data.get('tagline', 'Experience the difference'),
                    social_caption=copy_data.get('social_caption', f'Discover {product_input.product_name} ✨'),
                    ad_copy=copy_data.get('ad_copy', 'Transform your everyday experience.'),
                    email_subject=copy_data.get('email_subject', 'Something special awaits'),
                    product_description=copy_data.get('product_description', product_input.product_description)
                ))
                logger.info(f"Successfully generated copy for: {persona.name}")
            else:
                raise ValueError("Invalid copy data from OpenAI")
                
        except Exception as e:
            logger.error(f"Copy generation error: {e}")
            copies.append(create_fallback_copy(product_input, persona))
    
    return copies

def create_fallback_copy(product_input: ProductInput, persona: TastePersona) -> CampaignCopy:
    """Fallback copy when generation fails"""
    return CampaignCopy(
        persona_id=persona.persona_id,
        tagline=f"{product_input.product_name} - Crafted for You",
        social_caption=f"Meet {product_input.product_name} ✨ Where {product_input.brand_values[0] if product_input.brand_values else 'innovation'} meets style. Join our community! 🌟",
        ad_copy=f"Discover {product_input.product_name}. Thoughtfully designed for those who value {', '.join(product_input.brand_values[:2]) if product_input.brand_values else 'quality and innovation'}.",
        email_subject=f"Introducing {product_input.product_name[:30]}",
        product_description=f"{product_input.product_name} is more than a product - it's a statement of your values. {product_input.product_description}"
    )

async def generate_suggestions(product_input: ProductInput, personas: List[TastePersona]) -> Dict[str, List[str]]:
    """Generate marketing suggestions based on personas and their interests"""
    all_interests = {}
    for persona in personas:
        for category, interests in persona.cultural_interests.items():
            if category not in all_interests:
                all_interests[category] = set()
            all_interests[category].update(interests)
    
    # Get top interests
    top_music = list(all_interests.get('music', []))[:2]
    top_fashion = list(all_interests.get('fashion', []))[:2]
    top_dining = list(all_interests.get('dining', []))[:2]
    
    suggestions = {
        "content_themes": [
            f"Behind the {product_input.product_name} story",
            "Customer spotlight: Real stories, real impact",
            f"The {product_input.brand_values[0] if product_input.brand_values else 'innovation'} guide",
            "Day in the life with our products"
        ],
        "partnership_ideas": [
            f"Collaborate with {top_music[0] if top_music else 'indie'} music artists",
            f"Partner with {top_fashion[0] if top_fashion else 'sustainable'} fashion brands",
            f"Pop-ups at {top_dining[0] if top_dining else 'local'} venues",
            "Co-create with cultural tastemakers"
        ],
        "campaign_angles": [
            f"The {product_input.brand_values[0] if product_input.brand_values else 'future'} starts here",
            "Join the movement",
            "Elevate your everyday",
            "Where values meet style"
        ],
        "visual_directions": [
            "Minimalist product photography",
            "Lifestyle shots in natural settings",
            "User-generated content campaigns",
            "Bold typography with clean layouts"
        ]
    }
    
    return suggestions

# API Endpoints
@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Test connections
    qloo_connected = bool(QLOO_API_KEY)
    openai_connected = bool(OPENAI_API_KEY)
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="3.0.0",
        qloo_connected=qloo_connected,
        openai_connected=openai_connected
    )

@app.post("/api/generate-targeting", response_model=TasteTargetResponse)
async def generate_targeting(product_input: ProductInput):
    """Generate taste-based targeting using Qloo + OpenAI"""
    try:
        logger.info(f"Generating targeting for: {product_input.product_name}")
        logger.info(f"Using Qloo API: {bool(QLOO_API_KEY)}")
        logger.info(f"Using OpenAI API: {bool(OPENAI_API_KEY)}")
        
        # Step 1: Get taste clusters from Qloo API
        taste_clusters = await call_qloo_api(product_input.dict())
        logger.info(f"Retrieved {len(taste_clusters)} taste clusters")
        
        # Step 2: Generate personas using OpenAI
        personas = await generate_personas_with_openai(product_input, taste_clusters)
        logger.info(f"Generated {len(personas)} personas")
        
        # Step 3: Generate campaign copy
        campaign_copies = await generate_campaign_copy_with_openai(product_input, personas)
        logger.info(f"Generated {len(campaign_copies)} copy variations")
        
        # Step 4: Generate suggestions
        suggestions = await generate_suggestions(product_input, personas)
        
        # Determine data source
        data_source = "Qloo Taste AI + OpenAI GPT-4" if QLOO_API_KEY else "OpenAI GPT-4 (Mock Qloo Data)"
        
        response = TasteTargetResponse(
            product_name=product_input.product_name,
            personas=personas,
            campaign_copies=campaign_copies,
            generation_timestamp=datetime.utcnow().isoformat(),
            suggestions=suggestions,
            data_source=data_source
        )
        
        logger.info(f"Successfully generated targeting for: {product_input.product_name}")
        return response
        
    except Exception as e:
        logger.error(f"Error in generate_targeting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-openai")
async def test_openai_connection():
    """Test OpenAI API connection"""
    try:
        response = await call_openai_api("Hello! Please respond with: 'OpenAI connection successful!'")
        return {
            "status": "success",
            "response": response,
            "model": "gpt-4o-mini"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/test-visual-generation")
async def test_visual_generation():
    """Test visual generation capability"""
    try:
        # Test if Hugging Face Space is accessible
        try:
            client = Client("Samkelo28/taste-target-visual-generator")
            status = "connected"
            message = "Hugging Face Space is accessible"
        except Exception as e:
            status = "fallback"
            message = f"Using local generation (HF Space error: {str(e)})"
        
        # Test local generation
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        local_status = "available"
        
        return {
            "huggingface_space": {
                "status": status,
                "message": message,
                "space_url": "https://huggingface.co/spaces/Samkelo28/taste-target-visual-generator"
            },
            "local_generation": {
                "status": local_status,
                "message": "Local generation available as fallback"
            },
            "recommendation": "Visual generation is ready to use"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/test-connections")
async def test_connections():
    """Test all API connections"""
    results = {
        "qloo": {"configured": bool(QLOO_API_KEY), "status": "unknown"},
        "openai": {"configured": bool(OPENAI_API_KEY), "status": "unknown"},
        "visual_generation": {"configured": True, "status": "unknown"}
    }
    
    # Test Qloo
    if QLOO_API_KEY:
        try:
            headers = {"X-Api-Key": QLOO_API_KEY}
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"{QLOO_API_URL}/v2/insights?filter.type=urn:demographics&signal.interests.tags=urn:tag:genre:lifestyle:general"
                response = await client.get(url, headers=headers)
                results["qloo"]["status"] = "connected" if response.status_code == 200 else "error"
        except:
            results["qloo"]["status"] = "error"
    
    # Test OpenAI
    if OPENAI_API_KEY:
        try:
            test_result = await test_openai_connection()
            results["openai"]["status"] = "connected" if test_result["status"] == "success" else "error"
        except:
            results["openai"]["status"] = "error"
    
    # Test Visual Generation
    try:
        visual_test = await test_visual_generation()
        results["visual_generation"]["status"] = "connected" if visual_test.get("huggingface_space", {}).get("status") == "connected" else "fallback"
    except:
        results["visual_generation"]["status"] = "fallback"
    
    return results

@app.post("/api/generate-visual")
async def generate_visual(request: VisualGenerationRequest):
    """Generate marketing visual using Hugging Face Space"""
    # [Your existing code remains exactly the same]
    try:
        logger.info(f"Generating visual for persona: {request.persona_name}")
        
        # Try to use the Hugging Face Space first
        try:
            # Initialize Gradio client for your Space
            logger.info(f"Attempting to use Hugging Face Space for visual generation")
            
            client = Client("Samkelo28/taste-target-visual-generator")
            
            # Call the Space with your parameters
            result = await asyncio.to_thread(
                client.predict,
                request.persona_name,
                request.brand_values,
                request.product_description,
                request.style_preference,
                request.image_type,
                api_name="/predict"
            )
            
            # The result should be a file path to the generated image
            if result and isinstance(result, str) and os.path.exists(result):
                # Read the image file and convert to base64
                with open(result, "rb") as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                
                # Clean up the temporary file
                try:
                    os.remove(result)
                except:
                    pass
                
                logger.info(f"Successfully generated visual for {request.persona_name}")
                
                return {
                    "status": "success",
                    "image_data": f"data:image/png;base64,{img_base64}",
                    "message": "Visual generated successfully with AI"
                }
            else:
                raise Exception("Invalid result from Hugging Face Space")
                
        except Exception as hf_error:
            logger.warning(f"Hugging Face Space error: {str(hf_error)}")
            logger.info("Falling back to local generation")
            
            # [Rest of your existing fallback code remains the same]
            # Fallback: Generate a stylized placeholder image locally
            from PIL import Image, ImageDraw, ImageFont
            import io
            import math
            
            # Create a high-quality placeholder based on style
            width, height = 512, 512
            
            # Style-specific colors and designs
            style_configs = {
                "minimalist clean": {
                    "bg_color": (250, 250, 250),
                    "accent_color": (0, 0, 0),
                    "text_color": (0, 0, 0),
                    "font_size": 24
                },
                "bold vibrant": {
                    "bg_color": (255, 0, 128),
                    "accent_color": (0, 255, 255),
                    "text_color": (255, 255, 255),
                    "font_size": 32
                },
                "luxury premium": {
                    "bg_color": (20, 20, 20),
                    "accent_color": (218, 165, 32),
                    "text_color": (218, 165, 32),
                    "font_size": 28
                },
                "natural organic": {
                    "bg_color": (245, 245, 220),
                    "accent_color": (34, 139, 34),
                    "text_color": (34, 139, 34),
                    "font_size": 26
                },
                "tech futuristic": {
                    "bg_color": (10, 10, 50),
                    "accent_color": (0, 255, 255),
                    "text_color": (0, 255, 255),
                    "font_size": 30
                },
                "artistic creative": {
                    "bg_color": (255, 245, 238),
                    "accent_color": (255, 69, 0),
                    "text_color": (139, 69, 19),
                    "font_size": 28
                }
            }
            
            config = style_configs.get(request.style_preference, style_configs["minimalist clean"])
            
            # Create image with anti-aliasing
            img = Image.new('RGBA', (width, height), (*config["bg_color"], 255))
            draw = ImageDraw.Draw(img)
            
            # Generate logo design based on type
            if request.image_type == "logo":
                # Extract brand initials
                brand_name = request.product_description.strip()
                initials = ''.join([word[0].upper() for word in brand_name.split()[:2]])
                if not initials:
                    initials = brand_name[:2].upper()
                
                # Create logo based on style
                if request.style_preference == "minimalist clean":
                    # Circular logo with initials
                    draw.ellipse([156, 156, 356, 356], outline=config["accent_color"], width=4)
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
                    except:
                        font = ImageFont.load_default()
                    bbox = draw.textbbox((0, 0), initials, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    draw.text((256 - text_width//2, 256 - text_height//2), initials, 
                             fill=config["accent_color"], font=font)
                    
                elif request.style_preference == "bold vibrant":
                    # Gradient-style square logo
                    for i in range(100):
                        alpha = int(255 * (1 - i/100))
                        color = (*config["accent_color"], alpha)
                        draw.rectangle([156+i, 156+i, 356-i, 356-i], outline=color, width=2)
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
                    except:
                        font = ImageFont.load_default()
                    draw.text((256, 256), initials, fill=config["text_color"], font=font, anchor="mm")
                    
                elif request.style_preference == "luxury premium":
                    # Diamond shape with gold accent
                    points = [(256, 106), (406, 256), (256, 406), (106, 256)]
                    draw.polygon(points, outline=config["accent_color"], width=3)
                    # Inner diamond
                    inner_points = [(256, 156), (356, 256), (256, 356), (156, 256)]
                    draw.polygon(inner_points, outline=config["accent_color"], width=2)
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 42)
                    except:
                        font = ImageFont.load_default()
                    draw.text((256, 256), initials, fill=config["accent_color"], font=font, anchor="mm")
                    
                elif request.style_preference == "natural organic":
                    # Leaf-inspired logo
                    # Draw leaf shapes
                    for angle in range(0, 360, 45):
                        x = 256 + 80 * (angle % 90) / 90
                        y = 256 - 80 * (angle % 90) / 90
                        draw.arc([x-40, y-40, x+40, y+40], angle, angle+90, 
                                fill=config["accent_color"], width=3)
                    # Center circle
                    draw.ellipse([226, 226, 286, 286], fill=config["bg_color"], outline=config["accent_color"], width=3)
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
                    except:
                        font = ImageFont.load_default()
                    draw.text((256, 256), initials, fill=config["accent_color"], font=font, anchor="mm")
                    
                elif request.style_preference == "tech futuristic":
                    # Hexagon tech logo
                    hex_points = []
                    for i in range(6):
                        angle = i * 60 * math.pi / 180
                        x = 256 + 100 * math.cos(angle)
                        y = 256 + 100 * math.sin(angle)
                        hex_points.append((x, y))
                    draw.polygon(hex_points, outline=config["accent_color"], width=3)
                    # Inner hex
                    inner_hex = []
                    for i in range(6):
                        angle = i * 60 * math.pi / 180
                        x = 256 + 60 * math.cos(angle)
                        y = 256 + 60 * math.sin(angle)
                        inner_hex.append((x, y))
                    draw.polygon(inner_hex, outline=config["accent_color"], width=2)
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
                    except:
                        font = ImageFont.load_default()
                    draw.text((256, 256), initials, fill=config["accent_color"], font=font, anchor="mm")
                    
                else:  # artistic creative
                    # Abstract artistic logo
                    import random
                    random.seed(hash(brand_name))
                    for _ in range(8):
                        x1 = random.randint(156, 256)
                        y1 = random.randint(156, 256)
                        x2 = random.randint(256, 356)
                        y2 = random.randint(256, 356)
                        draw.arc([x1, y1, x2, y2], 0, 180, fill=config["accent_color"], width=3)
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)
                    except:
                        font = ImageFont.load_default()
                    draw.text((256, 256), initials, fill=config["accent_color"], font=font, anchor="mm")
                
                # Add brand name below logo
                try:
                    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                except:
                    small_font = ImageFont.load_default()
                
                draw.text((256, 420), brand_name, fill=config["text_color"], 
                         font=small_font, anchor="mt")
                
            else:
                # Marketing visual generation (existing code)
                if request.style_preference == "minimalist clean":
                    draw.ellipse([156, 156, 356, 356], outline=config["accent_color"], width=3)
                elif request.style_preference == "bold vibrant":
                    draw.rectangle([100, 100, 300, 300], fill=config["accent_color"])
                    draw.ellipse([212, 212, 412, 412], fill=config["bg_color"])
                elif request.style_preference == "luxury premium":
                    draw.rectangle([106, 206, 406, 306], fill=config["accent_color"])
                elif request.style_preference == "natural organic":
                    for i in range(5):
                        x = 256 + i * 30 - 60
                        y = 256 + i * 20 - 40
                        draw.ellipse([x-50, y-20, x+50, y+20], fill=config["accent_color"])
                elif request.style_preference == "tech futuristic":
                    for i in range(0, width, 50):
                        draw.line([(i, 0), (i, height)], fill=config["accent_color"], width=1)
                        draw.line([(0, i), (width, i)], fill=config["accent_color"], width=1)
                else:
                    draw.arc([100, 100, 400, 400], 0, 270, fill=config["accent_color"], width=5)
                
                # Add text
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", config["font_size"])
                except:
                    font = ImageFont.load_default()
                
                text = request.persona_name
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_x = (width - text_width) // 2
                draw.text((text_x, height - 80), text, fill=config["text_color"], font=font)
                
                product_text = request.product_description[:30] + "..." if len(request.product_description) > 30 else request.product_description
                try:
                    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                except:
                    small_font = ImageFont.load_default()
                
                bbox = draw.textbbox((0, 0), product_text, font=small_font)
                text_width = bbox[2] - bbox[0]
                text_x = (width - text_width) // 2
                draw.text((text_x, height - 50), product_text, fill=config["text_color"], font=small_font)
            
            # Add TasteTarget watermark for marketing visuals only
            if request.image_type != "logo":
                watermark = "TasteTarget AI"
                bbox = draw.textbbox((0, 0), watermark, font=small_font)
                draw.text((10, height - 20), watermark, fill=config["text_color"], font=small_font)
            
            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG', quality=95)
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            message = "Logo generated successfully" if request.image_type == "logo" else "Visual generated successfully"
            
            return {
                "status": "success",
                "image_data": f"data:image/png;base64,{img_base64}",
                "message": f"{message} (local generation)"
            }
                
    except Exception as e:
        logger.error(f"Visual generation error: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to generate visual: {str(e)}"
        }


# ADD THIS NEW ENDPOINT AFTER THE EXISTING generate_visual ENDPOINT
@app.post("/api/generate-cultural-visual")
async def generate_cultural_visual(request: dict):
    """Generate visuals that incorporate cultural insights from Qloo data"""
    try:
        persona_data = request.get("persona_data", {})
        product_info = request.get("product_info", {})
        visual_type = request.get("visual_type", "poster")
        style_preference = request.get("style_preference", "minimalist clean")
        custom_elements = request.get("custom_elements", "")
        
        # Extract cultural interests
        cultural_interests = persona_data.get("cultural_interests", {})
        psychographics = persona_data.get("psychographics", [])
        persona_name = persona_data.get("name", "Target Customer")
        
        # Build a culturally-informed description
        cultural_description = f"{product_info.get('name', 'product')}"
        
        # Add cultural elements to the description for better AI generation
        cultural_context = []
        
        if custom_elements:
            cultural_description += f" - {custom_elements}"
        else:
            # Add cultural context based on interests
            if cultural_interests.get("music"):
                music_styles = ', '.join(cultural_interests['music'][:2])
                cultural_context.append(f"inspired by {music_styles} vibes")
                
            if cultural_interests.get("fashion"):
                fashion_style = cultural_interests['fashion'][0] if cultural_interests['fashion'] else ""
                if fashion_style:
                    cultural_context.append(f"{fashion_style} aesthetic")
                    
            if cultural_interests.get("dining"):
                dining_pref = cultural_interests['dining'][0] if cultural_interests['dining'] else ""
                if dining_pref:
                    cultural_context.append(f"appeals to {dining_pref} enthusiasts")
                    
            if psychographics:
                cultural_context.append(f"designed for {psychographics[0]} mindset")
        
        # Combine cultural context into description
        if cultural_context:
            cultural_description += " - " + ", ".join(cultural_context)
        
        logger.info(f"Generating culturally-informed visual for persona: {persona_name}")
        logger.info(f"Cultural elements being incorporated: {cultural_interests}")
        logger.info(f"Enhanced description: {cultural_description}")
        
        # Determine image type
        image_type = "logo" if visual_type == "logo" and not custom_elements else "marketing"
        
        # Create a visual request with cultural enhancements
        visual_request = VisualGenerationRequest(
            persona_name=persona_name,
            brand_values=product_info.get('brand_values', 'quality, innovation'),
            product_description=cultural_description,
            style_preference=style_preference,
            image_type=image_type
        )
        
        # Use the existing generate_visual function with enhanced description
        result = await generate_visual(visual_request)
        
        # Add cultural metadata to the result
        if result.get("status") == "success":
            result["cultural_elements"] = cultural_interests
            result["psychographics"] = psychographics
            result["generation_type"] = "cultural_enhanced"
            result["prompt_summary"] = f"Created for {persona_name} with {len(psychographics)} key traits and {len(cultural_context)} cultural elements"
            
            # Log successful cultural generation
            logger.info(f"Successfully generated cultural visual for {persona_name} with {len(cultural_context)} cultural elements")
        
        return result
        
    except Exception as e:
        logger.error(f"Cultural visual generation error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Fallback to standard generation if cultural generation fails
        try:
            logger.info("Attempting fallback to standard visual generation")
            
            # Create a basic visual request
            basic_request = VisualGenerationRequest(
                persona_name=request.get("persona_data", {}).get("name", "Customer"),
                brand_values=request.get("product_info", {}).get("brand_values", "quality"),
                product_description=request.get("product_info", {}).get("name", "Product"),
                style_preference=request.get("style_preference", "minimalist clean"),
                image_type="logo" if request.get("visual_type") == "logo" else "marketing"
            )
            
            result = await generate_visual(basic_request)
            result["generation_type"] = "fallback"
            return result
            
        except Exception as fallback_error:
            logger.error(f"Fallback generation also failed: {str(fallback_error)}")
            return {
                "status": "error",
                "message": f"Failed to generate visual: {str(e)}"
            }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting TasteTarget API with Qloo + OpenAI...")
    logger.info(f"Qloo API: {'Connected' if QLOO_API_KEY else 'Not configured'}")
    logger.info(f"OpenAI API: {'Connected' if OPENAI_API_KEY else 'Not configured'}")
    logger.info("Visual Generation: Available via Hugging Face Space")
    uvicorn.run(app, host="0.0.0.0", port=8000)
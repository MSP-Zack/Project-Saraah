"""
Vision Integration for Image Generation
Allows Sarah to view, analyze, and understand generated images
Also handles image analysis for vision-based understanding
"""

import asyncio
import base64
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import io
from PIL import Image

from .types import GeneratedImage, ImageMetadata


class ImageVisionAnalyzer:
    """
    Analyzes images and provides descriptions
    Integrates with Sarah's vision capabilities
    """
    
    def __init__(self):
        self.analyzer_name = "Image Vision Analyzer"
        self.supported_formats = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"]
        print(f"[VISION]: {self.analyzer_name} initialized")
    
    async def analyze_image(self, image_data: bytes, analysis_type: str = "detailed") -> Dict[str, Any]:
        """
        Analyze an image and provide comprehensive information
        Returns: composition, objects, colors, style, mood, etc.
        """
        try:
            # Load image
            img = Image.open(io.BytesIO(image_data))
            
            analysis = {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "size_kb": len(image_data) / 1024,
                "mode": img.mode,
            }
            
            if analysis_type == "detailed":
                # Extract dominant colors
                analysis["dominant_colors"] = await self._extract_dominant_colors(img)
                
                # Get image characteristics
                analysis["characteristics"] = {
                    "aspect_ratio": f"{img.width}:{img.height}",
                    "orientation": "landscape" if img.width > img.height else "portrait" if img.height > img.width else "square",
                    "brightness": await self._estimate_brightness(img),
                    "saturation": await self._estimate_saturation(img),
                }
            
            return analysis
            
        except Exception as e:
            print(f"[VISION]: Image analysis failed: {e}")
            return {"error": str(e)}
    
    async def _extract_dominant_colors(self, img: Image.Image) -> List[Dict[str, Any]]:
        """Extract dominant colors from image"""
        try:
            # Resize for faster analysis
            small_img = img.copy()
            small_img.thumbnail((100, 100))
            
            # Get colors
            pixels = list(small_img.getdata())
            if not pixels:
                return []
            
            # Count color frequencies
            from collections import Counter
            color_counts = Counter(pixels)
            
            # Get top 5 colors
            top_colors = color_counts.most_common(5)
            
            colors = []
            for color, count in top_colors:
                if isinstance(color, tuple):
                    colors.append({
                        "rgb": color[:3] if len(color) >= 3 else color,
                        "frequency": count / len(pixels)
                    })
            
            return colors
        except Exception as e:
            print(f"[VISION]: Color extraction failed: {e}")
            return []
    
    async def _estimate_brightness(self, img: Image.Image) -> float:
        """Estimate overall brightness (0-1)"""
        try:
            # Convert to grayscale
            gray = img.convert("L")
            pixels = list(gray.getdata())
            
            if not pixels:
                return 0.5
            
            avg_brightness = sum(pixels) / len(pixels)
            return avg_brightness / 255.0
        except:
            return 0.5
    
    async def _estimate_saturation(self, img: Image.Image) -> float:
        """Estimate overall saturation (0-1)"""
        try:
            # Convert to HSV would be better but PIL doesn't support it directly
            # Use a simple approximation based on color range
            rgb_img = img.convert("RGB")
            pixels = list(rgb_img.getdata())
            
            if not pixels:
                return 0.5
            
            total_saturation = 0
            for pixel in pixels:
                r, g, b = pixel
                max_val = max(r, g, b)
                min_val = min(r, g, b)
                
                if max_val == 0:
                    saturation = 0
                else:
                    saturation = (max_val - min_val) / max_val
                
                total_saturation += saturation
            
            avg_saturation = total_saturation / len(pixels)
            return min(avg_saturation, 1.0)
        except:
            return 0.5
    
    async def get_image_description(self, image_data: bytes, huggingface_model: Optional[str] = None, huggingface_api_key: Optional[str] = None) -> str:
        """
        Get a natural language description of the image.
        Uses Hugging Face vision captioning if configured, otherwise falls back to local analysis.
        """
        try:
            if huggingface_model and huggingface_api_key:
                hf_description = await self._get_huggingface_description(image_data, huggingface_model, huggingface_api_key)
                if hf_description:
                    return hf_description

            analysis = await self.analyze_image(image_data, "detailed")
            
            if "error" in analysis:
                return "Unable to analyze image"
            
            desc = f"An image with dimensions {analysis['width']}x{analysis['height']} pixels"
            
            if "characteristics" in analysis:
                chars = analysis["characteristics"]
                desc += f", approximately {chars['orientation']}"
                
                if chars['brightness'] < 0.3:
                    desc += ", quite dark"
                elif chars['brightness'] > 0.7:
                    desc += ", very bright"
                
                if chars['saturation'] < 0.3:
                    desc += ", with muted colors"
                elif chars['saturation'] > 0.7:
                    desc += ", with vibrant colors"
            
            if "dominant_colors" in analysis and analysis["dominant_colors"]:
                colors = analysis["dominant_colors"]
                color_names = []
                for color_info in colors[:2]:
                    rgb = color_info.get("rgb", (0, 0, 0))
                    color_name = await self._rgb_to_color_name(rgb)
                    color_names.append(color_name)
                
                if color_names:
                    desc += f", with dominant colors being {' and '.join(color_names)}"
            
            desc += "."
            return desc
            
        except Exception as e:
            print(f"[VISION]: Failed to generate description: {e}")
            return "Image analysis unavailable"

    async def _get_huggingface_description(self, image_data: bytes, model: str, api_key: str) -> str:
        """
        Use the Hugging Face Inference API to get a caption or description for an image.
        """
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/octet-stream"
            }
            url = f"https://api-inference.huggingface.co/models/{model}"

            def hf_request():
                return requests.post(url, headers=headers, data=image_data, timeout=90)

            response = await asyncio.to_thread(hf_request)
            if response.status_code != 200:
                print(f"[VISION]: Hugging Face model {model} returned {response.status_code}: {response.text}")
                return ""

            result = response.json()
            if isinstance(result, dict):
                if "generated_text" in result and result["generated_text"]:
                    return result["generated_text"].strip()
                if "text" in result and result["text"]:
                    return result["text"].strip()
                if "error" in result:
                    print(f"[VISION]: Hugging Face vision error: {result['error']}")
                    return ""

            if isinstance(result, list) and result:
                first = result[0]
                if isinstance(first, dict):
                    if "generated_text" in first and first["generated_text"]:
                        return first["generated_text"].strip()
                    if "text" in first and first["text"]:
                        return first["text"].strip()
                elif isinstance(first, str):
                    return first.strip()

            if isinstance(result, str):
                return result.strip()

            return ""
        except Exception as e:
            print(f"[VISION]: Hugging Face request failed: {e}")
            return ""
    
    async def _rgb_to_color_name(self, rgb: tuple) -> str:
        """Convert RGB to color name"""
        r, g, b = rgb[0], rgb[1], rgb[2]
        
        if r < 50 and g < 50 and b < 50:
            return "black"
        elif r > 200 and g > 200 and b > 200:
            return "white"
        elif r > g and r > b:
            if r > 100:
                return "red"
            else:
                return "dark red"
        elif g > r and g > b:
            if g > 100:
                return "green"
            else:
                return "dark green"
        elif b > r and b > g:
            if b > 100:
                return "blue"
            else:
                return "dark blue"
        elif r > 100 and g > 100 and b < 100:
            return "yellow"
        elif r < 100 and g > 100 and b > 100:
            return "cyan"
        elif r > 100 and g < 100 and b > 100:
            return "magenta"
        else:
            return "gray"
    
    async def compare_images(self, image1_data: bytes, image2_data: bytes) -> Dict[str, Any]:
        """Compare two images for similarity and differences"""
        try:
            analysis1 = await self.analyze_image(image1_data, "detailed")
            analysis2 = await self.analyze_image(image2_data, "detailed")
            
            comparison = {
                "image1_size": f"{analysis1.get('width')}x{analysis1.get('height')}",
                "image2_size": f"{analysis2.get('width')}x{analysis2.get('height')}",
                "format_match": analysis1.get("format") == analysis2.get("format"),
                "brightness_diff": abs(
                    analysis1.get("characteristics", {}).get("brightness", 0) -
                    analysis2.get("characteristics", {}).get("brightness", 0)
                ),
            }
            
            return comparison
            
        except Exception as e:
            print(f"[VISION]: Image comparison failed: {e}")
            return {"error": str(e)}


class ImageUnderstandingSystem:
    """
    Allows Sarah to understand and respond to images
    Integrates with the vision analyzer
    """
    
    def __init__(self):
        self.analyzer = ImageVisionAnalyzer()
        self.image_memory: Dict[str, Dict[str, Any]] = {}  # image_id -> analysis
        print("[VISION]: Image Understanding System initialized")
    
    async def process_generated_image(self, image: GeneratedImage) -> Dict[str, Any]:
        """
        Process a generated image so Sarah understands what she created
        """
        try:
            analysis = await self.analyzer.analyze_image(image.image_data, "detailed")
            description = await self.analyzer.get_image_description(image.image_data)
            
            image_understanding = {
                "image_id": image.image_id,
                "prompt_used": image.prompt,
                "model": image.model_used,
                "generated_by": "sarah",
                "analysis": analysis,
                "description": description,
                "created_at": image.created_at.isoformat(),
            }
            
            # Store in memory
            self.image_memory[image.image_id] = image_understanding
            
            return image_understanding
            
        except Exception as e:
            print(f"[VISION]: Failed to process generated image: {e}")
            return {"error": str(e)}
    
    async def understand_uploaded_image(self, image_path: str) -> Dict[str, Any]:
        """
        Understand an uploaded image that Sarah needs to see
        """
        try:
            path = Path(image_path)
            
            if not path.exists():
                return {"error": f"Image not found: {image_path}"}
            
            # Read image
            with open(path, 'rb') as f:
                image_data = f.read()
            
            analysis = await self.analyzer.analyze_image(image_data, "detailed")
            description = await self.analyzer.get_image_description(image_data)
            
            understanding = {
                "filename": path.name,
                "path": str(path),
                "analysis": analysis,
                "description": description,
                "file_size_kb": len(image_data) / 1024,
            }
            
            # Store in memory
            image_id = path.stem
            self.image_memory[image_id] = understanding
            
            return understanding
            
        except Exception as e:
            print(f"[VISION]: Failed to understand uploaded image: {e}")
            return {"error": str(e)}
    
    async def describe_image(self, image_id_or_path: str) -> str:
        """Get text description of an image"""
        # Check memory first
        if image_id_or_path in self.image_memory:
            return self.image_memory[image_id_or_path].get("description", "")
        
        # Try as file path
        if Path(image_id_or_path).exists():
            with open(image_id_or_path, 'rb') as f:
                image_data = f.read()
            return await self.analyzer.get_image_description(image_data)
        
        return ""
    
    async def get_image_context(self, image_id: str) -> Dict[str, Any]:
        """Get full understanding/context of an image"""
        if image_id in self.image_memory:
            return self.image_memory[image_id]
        return {}

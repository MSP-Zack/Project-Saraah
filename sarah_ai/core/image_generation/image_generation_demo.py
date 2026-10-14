"""
Demo and test script for the image generation system
"""

import asyncio
from pathlib import Path

from .engine import ImageGenerationEngine


async def run_demo():
    engine = ImageGenerationEngine(storage_path=Path("./images"))
    await engine.initialize()

    print("=== Image Generation Demo ===")
    print("Current settings:", await engine.get_stats())

    # Generate a sample image if the provider is configured
    if engine.current_provider and engine.current_provider.is_available:
        print("Generating sample image...")
        try:
            image = await engine.generate_image(
                prompt="A futuristic city skyline at sunset with neon lights and flying cars",
                width=1024,
                height=1024,
                quality=engine.settings.default_quality,
            )
            
            if image.image_data:
                print("Sample image generated successfully")
                await engine.save_image(image)
            else:
                print("Image generation returned empty data")
        except Exception as e:
            print("Demo generation failed:", e)
    else:
        print("No image provider available. Please configure Hugging Face or Replicate API keys.")


if __name__ == "__main__":
    asyncio.run(run_demo())

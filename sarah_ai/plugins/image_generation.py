import json
import os
import re
import base64
import asyncio
import random
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests
from PIL import Image, ImageDraw, ImageFont


class ImageGenerator:
    """Plugin-backed image generation and search support."""

    def __init__(self):
        self.name = "image_generation"
        self.description = "Search, download, and generate image assets for Sarah."
        self.version = "1.0"
        self.data_dir = Path(__file__).parent.parent / "static" / "generated_images"
        self.history_path = Path(__file__).parent.parent / "image_history.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history = self._load_history()

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
        }

    def _load_history(self) -> List[Dict[str, Any]]:
        if self.history_path.exists():
            try:
                return json.loads(self.history_path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_history(self) -> None:
        self.history_path.write_text(json.dumps(self.history[-100:], indent=2), encoding="utf-8")

    def _record(self, entry: Dict[str, Any]) -> None:
        entry["timestamp"] = datetime.now().isoformat()
        entry["id"] = str(int(datetime.now().timestamp() * 1000)) + f"-{random.randint(100,999)}"
        self.history.insert(0, entry)
        self._save_history()

    def _safe_url(self, url: str) -> str:
        if not url or not url.startswith(('http://', 'https://')):
            raise ValueError("Invalid URL")
        return url

    async def search(self, query: str, source: str = "bing", limit: int = 12) -> Dict[str, Any]:
        if not query:
            return {"success": False, "error": "Query cannot be empty"}

        query = query.strip()
        if source not in ["bing", "unsplash", "pexels"]:
            source = "bing"

        results = []
        try:
            if source == "bing":
                results = await asyncio.to_thread(self._search_bing, query, limit)
            elif source == "unsplash":
                results = await asyncio.to_thread(self._search_unsplash, query, limit)
            elif source == "pexels":
                results = await asyncio.to_thread(self._search_pexels, query, limit)
        except Exception as e:
            return {"success": False, "error": str(e)}

        self._record({"type": "search", "query": query, "source": source, "results": [r["url"] for r in results]})
        return {"success": True, "results": results}

    def _search_bing(self, query: str, limit: int) -> List[Dict[str, Any]]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.bing.com/images/search?q={encoded}&form=HDRSC2"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text

        matches = re.findall(r'"murl":"(https?://[^"]+)"', html)
        unique = []
        for match in matches:
            cleaned = match.replace('\\u0026', '&')
            if cleaned not in unique:
                unique.append(cleaned)
            if len(unique) >= limit:
                break

        trimmed = []
        for index, image_url in enumerate(unique):
            trimmed.append({
                "id": f"bing-{index}-{hash(image_url) % 10000}",
                "title": query,
                "thumbnail": image_url,
                "url": image_url,
                "source": "Bing"
            })
        return trimmed

    def _search_unsplash(self, query: str, limit: int) -> List[Dict[str, Any]]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://unsplash.com/s/photos/{encoded}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text
        matches = re.findall(r'srcset="([^"]+)"', html)
        unique = []
        for match in matches:
            url_candidate = match.split(' ')[0]
            if url_candidate.startswith('http') and url_candidate not in unique:
                unique.append(url_candidate)
            if len(unique) >= limit:
                break
        return [{
            "id": f"unsplash-{i}-{hash(url) % 10000}",
            "title": query,
            "thumbnail": url,
            "url": url,
            "source": "Unsplash"
        } for i, url in enumerate(unique)]

    def _search_pexels(self, query: str, limit: int) -> List[Dict[str, Any]]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.pexels.com/search/{encoded}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text
        matches = re.findall(r'<img[^>]+src="(https?://images\.pexels\.com/photos/[^"]+)"', html)
        unique = []
        for match in matches:
            if match not in unique:
                unique.append(match)
            if len(unique) >= limit:
                break
        return [{
            "id": f"pexels-{i}-{hash(url) % 10000}",
            "title": query,
            "thumbnail": url,
            "url": url,
            "source": "Pexels"
        } for i, url in enumerate(unique)]

    async def download(self, url: str, filename: Optional[str] = None) -> Dict[str, Any]:
        try:
            clean_url = self._safe_url(url)
            file_bytes, content_type = await asyncio.to_thread(self._fetch_binary, clean_url)
            ext = self._infer_extension(clean_url, content_type)
            name = filename.strip() if filename else None
            if not name:
                name = f"img_{int(datetime.now().timestamp())}_{random.randint(100,999)}.{ext}"
            else:
                if not name.lower().endswith(ext):
                    name = f"{name}.{ext}"
            dest = self.data_dir / name
            dest.write_bytes(file_bytes)
            url_path = f"/static/generated_images/{dest.name}"
            self._record({"type": "download", "url": clean_url, "path": url_path})
            return {"success": True, "url": url_path, "filename": dest.name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _fetch_binary(self, url: str) -> Any:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.content, response.headers.get("content-type", "application/octet-stream")

    def _infer_extension(self, url: str, content_type: str) -> str:
        if content_type.startswith("image/"):
            ext = content_type.split("/")[1].split(";")[0]
            if ext == "jpeg":
                ext = "jpg"
            return ext
        if url.lower().endswith('.png'):
            return 'png'
        if url.lower().endswith('.jpg') or url.lower().endswith('.jpeg'):
            return 'jpg'
        if url.lower().endswith('.gif'):
            return 'gif'
        return 'png'

    async def generate(self, prompt: str, style: str = "creative", count: int = 1) -> Dict[str, Any]:
        if not prompt:
            return {"success": False, "error": "Prompt cannot be empty"}

        images = []
        for i in range(max(1, min(4, count))):
            generated = await asyncio.to_thread(self._create_placeholder_image, prompt, style, i)
            images.append(generated)

        self._record({"type": "generate", "prompt": prompt, "style": style, "images": images})
        return {"success": True, "images": images}

    def _create_placeholder_image(self, prompt: str, style: str, index: int) -> str:
        width, height = 1024, 1024
        image = Image.new("RGB", (width, height), self._random_color_palette())
        draw = ImageDraw.Draw(image)
        text = f"{prompt[:80]}"
        try:
            font = ImageFont.truetype("arial.ttf", 32)
        except Exception:
            font = ImageFont.load_default()

        margin = 40
        lines = self._wrap_text(text, font, width - margin * 2)
        y = height // 2 - (len(lines) * (font.size + 8)) // 2
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 72))
        image.paste(overlay, (0, 0), overlay)
        for line in lines:
            w, h = draw.textsize(line, font=font)
            draw.text(((width - w) / 2, y), line, fill=(255, 255, 255), font=font)
            y += h + 10

        filename = f"generated_{int(datetime.now().timestamp())}_{index}.png"
        dest = self.data_dir / filename
        image.save(dest, format="PNG")
        return f"/static/generated_images/{filename}"

    def _wrap_text(self, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            width = font.getsize(test)[0]
            if width <= max_width or not current:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def _random_color_palette(self) -> tuple:
        palettes = [
            (27, 38, 79),
            (18, 54, 60),
            (70, 19, 79),
            (37, 67, 86),
            (90, 30, 70),
        ]
        return random.choice(palettes)

    def list_images(self) -> List[str]:
        files = sorted(self.data_dir.glob('*'), key=lambda x: x.stat().st_mtime, reverse=True)
        return [f"/static/generated_images/{p.name}" for p in files if p.is_file()]

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history


class Plugin:
    def __init__(self):
        self.generator = ImageGenerator()

    def get_info(self) -> Dict[str, Any]:
        return self.generator.get_info()

    async def search(self, query: str, source: str = "bing", limit: int = 12) -> Dict[str, Any]:
        return await self.generator.search(query, source, limit)

    async def download(self, url: str, filename: Optional[str] = None) -> Dict[str, Any]:
        return await self.generator.download(url, filename)

    async def generate(self, prompt: str, style: str = "creative", count: int = 1) -> Dict[str, Any]:
        return await self.generator.generate(prompt, style, count)

    def list_images(self) -> List[str]:
        return self.generator.list_images()

    def get_history(self) -> List[Dict[str, Any]]:
        return self.generator.get_history()

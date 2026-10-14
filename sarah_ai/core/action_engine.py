import os
import sys
import json
import asyncio
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class ActionEngine:
    """
    Computer control engine allowing Sarah to interact with the system.
    Handles mouse, keyboard, file operations, browser, and application control.
    All operations are non-admin and user-safe.
    """
    
    def __init__(self):
        self.pyautogui_available = False
        self.pyperclip_available = False
        self.playwright_available = False
        self._browser_page = None
        self._playwright = None
        
        # Try importing optional dependencies
        try:
            import pyautogui
            self.pyautogui = pyautogui
            self.pyautogui.FAILSAFE = True
            self.pyautogui.PAUSE = 0.1
            self.pyautogui_available = True
        except ImportError:
            print("[ACTION]: pyautogui not available. Mouse/keyboard disabled.")
        
        try:
            import pyperclip
            self.pyperclip = pyperclip
            self.pyperclip_available = True
        except ImportError:
            print("[ACTION]: pyperclip not available.")
        
        try:
            from playwright.async_api import async_playwright
            self._async_playwright = async_playwright
            self.playwright_available = True
        except ImportError:
            print("[ACTION]: playwright not available. Browser control disabled.")
    
    # ========== MOUSE CONTROL ==========
    async def mouse_move(self, x: int, y: int, duration: float = 0.5) -> Dict:
        """Move mouse to screen coordinates."""
        if not self.pyautogui_available:
            return {"success": False, "error": "pyautogui not installed"}
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.pyautogui.moveTo, x, y, duration)
            return {"success": True, "x": x, "y": y}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def mouse_click(self, x: int = None, y: int = None, button: str = "left", clicks: int = 1) -> Dict:
        """Click at coordinates (or current position if None)."""
        if not self.pyautogui_available:
            return {"success": False, "error": "pyautogui not installed"}
        try:
            loop = asyncio.get_event_loop()
            if x is not None and y is not None:
                await loop.run_in_executor(None, self.pyautogui.click, x, y, clicks, 0.1, button)
            else:
                await loop.run_in_executor(None, self.pyautogui.click, clicks=clicks, interval=0.1, button=button)
            return {"success": True, "position": {"x": x, "y": y}, "button": button}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def mouse_scroll(self, amount: int) -> Dict:
        """Scroll mouse wheel. Positive = up, negative = down."""
        if not self.pyautogui_available:
            return {"success": False, "error": "pyautogui not installed"}
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.pyautogui.scroll, amount)
            return {"success": True, "amount": amount}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_mouse_position(self) -> Dict:
        """Get current mouse position."""
        if not self.pyautogui_available:
            return {"success": False, "error": "pyautogui not installed"}
        try:
            pos = self.pyautogui.position()
            return {"success": True, "x": pos.x, "y": pos.y}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_screen_size(self) -> Dict:
        """Get primary screen dimensions."""
        if not self.pyautogui_available:
            return {"success": False, "error": "pyautogui not installed"}
        try:
            size = self.pyautogui.size()
            return {"success": True, "width": size.width, "height": size.height}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== KEYBOARD CONTROL ==========
    async def type_text(self, text: str, interval: float = 0.01) -> Dict:
        """Type text at current cursor position."""
        if not self.pyautogui_available:
            return {"success": False, "error": "pyautogui not installed"}
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.pyautogui.typewrite, text, interval)
            return {"success": True, "text": text[:50]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def press_key(self, key: str) -> Dict:
        """Press a single key (e.g., 'enter', 'tab', 'ctrl')."""
        if not self.pyautogui_available:
            return {"success": False, "error": "pyautogui not installed"}
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.pyautogui.press, key)
            return {"success": True, "key": key}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def hotkey(self, *keys: str) -> Dict:
        """Press key combination (e.g., 'ctrl', 'c')."""
        if not self.pyautogui_available:
            return {"success": False, "error": "pyautogui not installed"}
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.pyautogui.hotkey, *keys)
            return {"success": True, "keys": list(keys)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== FILE OPERATIONS ==========
    def _safe_path(self, path: str) -> str:
        """Ensure path is within user's home directory for safety."""
        home = str(Path.home())
        abs_path = os.path.abspath(os.path.expanduser(path))
        # Only allow operations within user directory
        if not abs_path.startswith(home):
            abs_path = os.path.join(home, path.lstrip("/\\"))
        return abs_path
    
    async def list_directory(self, path: str = ".") -> Dict:
        """List files in a directory."""
        try:
            safe_path = self._safe_path(path)
            items = []
            for item in os.listdir(safe_path):
                full = os.path.join(safe_path, item)
                items.append({
                    "name": item,
                    "path": full,
                    "is_dir": os.path.isdir(full),
                    "size": os.path.getsize(full) if os.path.isfile(full) else 0
                })
            return {"success": True, "path": safe_path, "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def read_file(self, path: str) -> Dict:
        """Read contents of a text file."""
        try:
            safe_path = self._safe_path(path)
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "path": safe_path, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def write_file(self, path: str, content: str) -> Dict:
        """Create or overwrite a text file."""
        try:
            safe_path = self._safe_path(path)
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "path": safe_path, "bytes_written": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def append_file(self, path: str, content: str) -> Dict:
        """Append to a text file."""
        try:
            safe_path = self._safe_path(path)
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            with open(safe_path, 'a', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "path": safe_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def delete_file(self, path: str) -> Dict:
        """Delete a file."""
        try:
            safe_path = self._safe_path(path)
            os.remove(safe_path)
            return {"success": True, "path": safe_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_directory(self, path: str) -> Dict:
        """Create a directory."""
        try:
            safe_path = self._safe_path(path)
            os.makedirs(safe_path, exist_ok=True)
            return {"success": True, "path": safe_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def delete_directory(self, path: str) -> Dict:
        """Delete a directory and its contents."""
        try:
            safe_path = self._safe_path(path)
            shutil.rmtree(safe_path)
            return {"success": True, "path": safe_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== APPLICATION CONTROL ==========
    async def open_application(self, app_name: str) -> Dict:
        """Open an application by name."""
        try:
            # Platform-specific app opening
            if sys.platform == "win32":
                # Try to find the app
                common_apps = {
                    "pycharm": "pycharm64.exe",
                    "notepad": "notepad.exe",
                    "calculator": "calc.exe",
                    "browser": "start microsoft-edge:",
                    "chrome": "chrome.exe",
                    "firefox": "firefox.exe",
                    "explorer": "explorer.exe",
                    "vscode": "code.exe"
                }
                app_cmd = common_apps.get(app_name.lower(), app_name)
                subprocess.Popen(app_cmd, shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([app_name])
            return {"success": True, "app": app_name}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== BROWSER CONTROL (Playwright) ==========
    async def browser_open(self, url: str = "about:blank") -> Dict:
        """Open browser and navigate to URL."""
        if not self.playwright_available:
            return {"success": False, "error": "playwright not installed. Run: pip install playwright && playwright install"}
        try:
            if self._playwright is None:
                self._playwright = await self._async_playwright().start()
            browser = await self._playwright.chromium.launch(headless=False)
            self._browser_page = await browser.new_page()
            await self._browser_page.goto(url)
            return {"success": True, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def browser_navigate(self, url: str) -> Dict:
        """Navigate to a URL in the opened browser."""
        if self._browser_page is None:
            return await self.browser_open(url)
        try:
            await self._browser_page.goto(url)
            return {"success": True, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def browser_click(self, selector: str) -> Dict:
        """Click an element on the page."""
        if self._browser_page is None:
            return {"success": False, "error": "Browser not open"}
        try:
            await self._browser_page.click(selector)
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def browser_type(self, selector: str, text: str) -> Dict:
        """Type text into an input field."""
        if self._browser_page is None:
            return {"success": False, "error": "Browser not open"}
        try:
            await self._browser_page.fill(selector, text)
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def browser_screenshot(self) -> Dict:
        """Take screenshot of browser page."""
        if self._browser_page is None:
            return {"success": False, "error": "Browser not open"}
        try:
            screenshot_bytes = await self._browser_page.screenshot()
            import base64
            b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            return {"success": True, "screenshot": b64}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def browser_get_content(self) -> Dict:
        """Get page text content."""
        if self._browser_page is None:
            return {"success": False, "error": "Browser not open"}
        try:
            content = await self._browser_page.content()
            # Extract text
            text = await self._browser_page.evaluate("() => document.body.innerText")
            return {"success": True, "content": text[:5000], "url": self._browser_page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict:
        """Get engine capability status."""
        return {
            "mouse": self.pyautogui_available,
            "keyboard": self.pyautogui_available,
            "clipboard": self.pyperclip_available,
            "browser": self.playwright_available,
            "file": True,
            "applications": True
        }

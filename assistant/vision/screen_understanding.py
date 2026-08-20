import os
import re
import base64
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

from ..utils.logger import logger
from ..config import settings, DATA_DIR


SCREENSHOTS_DIR = Path(DATA_DIR) / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


class ScreenUnderstanding:
    def __init__(self, llm_provider: str = "auto", api_key: Optional[str] = None):
        self.llm_provider = llm_provider
        self.api_key = api_key
        self._pyautogui_available = None
        self._pytesseract_available = None
        self._pygetwindow_available = None
        self._pil_available = None

    def _check_pyautogui(self) -> bool:
        if self._pyautogui_available is not None:
            return self._pyautogui_available
        try:
            import pyautogui  # noqa: F401
            self._pyautogui_available = True
        except ImportError:
            self._pyautogui_available = False
            logger.warning("[ScreenUnderstanding] pyautogui not available; screenshots disabled.")
        return self._pyautogui_available

    def _check_pytesseract(self) -> bool:
        if self._pytesseract_available is not None:
            return self._pytesseract_available
        try:
            import pytesseract  # noqa: F401
            from PIL import Image  # noqa: F401
            self._pytesseract_available = True
        except ImportError:
            self._pytesseract_available = False
            logger.warning("[ScreenUnderstanding] pytesseract/PIL not available; OCR disabled.")
        return self._pytesseract_available

    def _check_pygetwindow(self) -> bool:
        if self._pygetwindow_available is not None:
            return self._pygetwindow_available
        try:
            import pygetwindow  # noqa: F401
            self._pygetwindow_available = True
        except ImportError:
            self._pygetwindow_available = False
            logger.warning("[ScreenUnderstanding] pygetwindow not available; window inspection disabled.")
        return self._pygetwindow_available

    def _check_pil(self) -> bool:
        if self._pil_available is not None:
            return self._pil_available
        try:
            from PIL import Image  # noqa: F401
            self._pil_available = True
        except ImportError:
            self._pil_available = False
            logger.warning("[ScreenUnderstanding] PIL/Pillow not available; image ops limited.")
        return self._pil_available

    def _default_save_path(self, prefix: str = "screen") -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return str(SCREENSHOTS_DIR / f"{prefix}_{ts}.png")

    def take_screenshot(self, save_path: Optional[str] = None) -> str:
        save_path = save_path or self._default_save_path("screenshot")
        if not self._check_pyautogui():
            logger.error("[ScreenUnderstanding] Cannot take screenshot: pyautogui missing.")
            raise RuntimeError("pyautogui is required for screenshots but is not installed.")
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(save_path)
            logger.info(f"[ScreenUnderstanding] Screenshot saved to {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"[ScreenUnderstanding] Screenshot failed: {e}")
            raise RuntimeError(f"Screenshot failed: {e}")

    def capture_screen_region(self, x: int, y: int, w: int, h: int, save_path: Optional[str] = None) -> str:
        save_path = save_path or self._default_save_path("region")
        if not self._check_pyautogui():
            logger.error("[ScreenUnderstanding] Cannot capture region: pyautogui missing.")
            raise RuntimeError("pyautogui is required for region capture but is not installed.")
        try:
            import pyautogui
            screenshot = pyautogui.screenshot(region=(int(x), int(y), int(w), int(h)))
            screenshot.save(save_path)
            logger.info(f"[ScreenUnderstanding] Region screenshot saved to {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"[ScreenUnderstanding] Region capture failed: {e}")
            raise RuntimeError(f"Region capture failed: {e}")

    def _has_vision_llm(self) -> bool:
        if self.api_key:
            return True
        return any([
            settings.openai_api_key,
            settings.gemini_api_key,
            settings.anthropic_api_key,
            settings.openrouter_api_key,
        ])

    def _encode_image(self, image_path: str) -> Optional[str]:
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"[ScreenUnderstanding] Image encode failed: {e}")
            return None

    def _call_vision_llm(self, image_path: str, prompt: str) -> Optional[str]:
        try:
            b64 = self._encode_image(image_path)
            if not b64:
                return None
            if settings.gemini_api_key or (self.llm_provider == "gemini" and self.api_key):
                return self._call_gemini_vision(b64, prompt)
            if settings.openai_api_key or (self.llm_provider == "openai" and self.api_key):
                return self._call_openai_vision(b64, prompt)
            if settings.openrouter_api_key or (self.llm_provider == "openrouter" and self.api_key):
                return self._call_openrouter_vision(b64, prompt)
            if settings.anthropic_api_key or (self.llm_provider == "anthropic" and self.api_key):
                return self._call_anthropic_vision(b64, prompt)
            return None
        except Exception as e:
            logger.error(f"[ScreenUnderstanding] Vision LLM call failed: {e}")
            return None

    def _call_gemini_vision(self, b64_image: str, prompt: str) -> Optional[str]:
        try:
            import requests
            api_key = self.api_key or settings.gemini_api_key
            if not api_key:
                return None
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/png", "data": b64_image}}
                    ]
                }]
            }
            r = requests.post(url, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                texts = [p.get("text", "") for p in parts if p.get("text")]
                result = " ".join(texts).strip()
                return result or None
            logger.warning(f"[ScreenUnderstanding] Gemini vision API error {r.status_code}: {r.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"[ScreenUnderstanding] Gemini vision call error: {e}")
            return None

    def _call_openai_vision(self, b64_image: str, prompt: str) -> Optional[str]:
        try:
            import requests
            api_key = self.api_key or settings.openai_api_key
            if not api_key:
                return None
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
                    ]
                }],
                "max_tokens": 1000,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content")
            logger.warning(f"[ScreenUnderstanding] OpenAI vision API error {r.status_code}: {r.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"[ScreenUnderstanding] OpenAI vision call error: {e}")
            return None

    def _call_openrouter_vision(self, b64_image: str, prompt: str) -> Optional[str]:
        try:
            import requests
            api_key = self.api_key or settings.openrouter_api_key
            if not api_key:
                return None
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "openai/gpt-4o-mini",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
                    ]
                }],
            }
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content")
            logger.warning(f"[ScreenUnderstanding] OpenRouter vision API error {r.status_code}: {r.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"[ScreenUnderstanding] OpenRouter vision call error: {e}")
            return None

    def _call_anthropic_vision(self, b64_image: str, prompt: str) -> Optional[str]:
        try:
            import requests
            api_key = self.api_key or settings.anthropic_api_key
            if not api_key:
                return None
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1024,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64_image}}
                    ]
                }],
            }
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                blocks = data.get("content", [])
                texts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
                result = " ".join(texts).strip()
                return result or None
            logger.warning(f"[ScreenUnderstanding] Anthropic vision API error {r.status_code}: {r.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"[ScreenUnderstanding] Anthropic vision call error: {e}")
            return None

    def describe_screen(self, prompt: str = "Describe what's on this screen in detail.") -> Dict[str, Any]:
        try:
            image_path = self.take_screenshot()
        except Exception as e:
            return {
                "text": f"Could not capture the screen: {e}",
                "image_path": None,
                "error": True,
            }
        if self._has_vision_llm():
            description = self._call_vision_llm(image_path, prompt)
            if description:
                return {
                    "text": description,
                    "image_path": image_path,
                }
        return {
            "text": f"Vision LLM not configured. Saved screenshot at {image_path}",
            "image_path": image_path,
            "warning": True,
        }

    def extract_text_from_screen(self) -> Dict[str, Any]:
        if not self._check_pytesseract():
            try:
                image_path = self.take_screenshot()
                return {
                    "text": f"OCR unavailable (pytesseract/PIL not installed). Saved screenshot at {image_path}",
                    "image_path": image_path,
                    "warning": True,
                }
            except Exception as e:
                return {
                    "text": f"OCR unavailable and screenshot failed: {e}",
                    "image_path": None,
                    "error": True,
                }
        try:
            import pytesseract
            from PIL import Image
            image_path = self.take_screenshot()
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return {
                "text": text.strip() or "(No readable text found on screen)",
                "image_path": image_path,
                "data": {"raw_text": text},
            }
        except Exception as e:
            logger.error(f"[ScreenUnderstanding] OCR extraction failed: {e}")
            return {
                "text": f"OCR extraction failed: {e}",
                "image_path": None,
                "error": True,
            }

    def debug_screen_error(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "suspicious_windows": [],
            "error_keywords_found": False,
            "image_path": None,
            "ocr_text": None,
        }
        try:
            result["image_path"] = self.take_screenshot()
        except Exception as e:
            logger.warning(f"[ScreenUnderstanding] Debug screenshot failed: {e}")
            result["screenshot_error"] = str(e)
        if self._check_pygetwindow():
            try:
                import pygetwindow as gw
                keywords = ["error", "traceback", "exception", "fatal", "failed", "fail", "crash"]
                for win in gw.getAllWindows():
                    title = (win.title or "").strip()
                    if not title:
                        continue
                    low = title.lower()
                    if any(k in low for k in keywords):
                        result["suspicious_windows"].append({
                            "title": title,
                            "left": win.left,
                            "top": win.top,
                            "width": win.width,
                            "height": win.height,
                        })
                if result["suspicious_windows"]:
                    result["error_keywords_found"] = True
            except Exception as e:
                logger.error(f"[ScreenUnderstanding] Window inspection failed: {e}")
                result["window_error"] = str(e)
        if self._check_pytesseract() and result.get("image_path"):
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(result["image_path"])
                text = pytesseract.image_to_string(img)
                result["ocr_text"] = text
                low_text = text.lower()
                keywords = ["error", "traceback", "exception", "fatal", "failed", "typeerror", "valueerror", "runtimeerror"]
                if any(k in low_text for k in keywords):
                    result["error_keywords_found"] = True
            except Exception as e:
                logger.warning(f"[ScreenUnderstanding] Debug OCR failed: {e}")
        count = len(result["suspicious_windows"])
        if result["error_keywords_found"]:
            result["text"] = (
                f"Debug scan complete. Found {count} suspicious window title(s) matching error keywords. "
                f"Screenshot saved at {result.get('image_path', 'N/A')}. "
                + (f"Suspicious windows: {', '.join(w['title'] for w in result['suspicious_windows'])}." if count else "")
            )
        else:
            result["text"] = (
                f"Debug scan complete. No obvious error keywords found in window titles. "
                f"Screenshot saved at {result.get('image_path', 'N/A')} for manual review."
            )
        return result

    @staticmethod
    def skill_handle(text: str, assistant_ref: Any = None) -> Optional[Dict[str, Any]]:
        if not isinstance(text, str):
            return None
        low = text.lower()
        su = ScreenUnderstanding()
        if re.search(r"\b(what(?:'s| is)? on my screen|describe (my |the )?screen|what am i looking at|look at my screen|tell me what('s| is) on screen)\b", low):
            try:
                res = su.describe_screen()
                return {
                    "text": res["text"],
                    "intent": "screen_describe",
                    "data": res,
                }
            except Exception as e:
                return {"text": f"Sorry, I couldn't capture your screen: {e}", "intent": "screen_describe", "error": True}
        if re.search(r"\b(read (the |me )?(text|words)|ocr|extract text|what does (this|the screen|it) say|read me the text)\b", low):
            try:
                res = su.extract_text_from_screen()
                return {
                    "text": f"Here's the text I found on your screen:\n\n{res['text']}",
                    "intent": "screen_ocr",
                    "data": res,
                }
            except Exception as e:
                return {"text": f"Sorry, I couldn't read text from your screen: {e}", "intent": "screen_ocr", "error": True}
        if re.search(r"\b(debug (this |the )?(error|screen|issue)|what('s| is) (this )?error|help me debug|find the error|diagnose this)\b", low):
            try:
                res = su.debug_screen_error()
                return {
                    "text": res["text"],
                    "intent": "screen_debug",
                    "data": res,
                }
            except Exception as e:
                return {"text": f"Sorry, error debugging failed: {e}", "intent": "screen_debug", "error": True}
        return None

import asyncio
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from ..utils.logger import logger

_EDGE_VOICES = {
    "en-US": {
        "male": "en-US-ChristopherNeural",
        "female": "en-US-JennyNeural",
        "neutral": "en-US-AriaNeural",
    },
    "en-GB": {
        "male": "en-GB-RyanNeural",
        "female": "en-GB-SoniaNeural",
    },
    "en-IN": {
        "male": "en-IN-PrabhatNeural",
        "female": "en-IN-NeerjaNeural",
    },
    "hi-IN": {
        "male": "hi-IN-MadhurNeural",
        "female": "hi-IN-KalpanaNeural",
    },
    "es-ES": {
        "male": "es-ES-AlvaroNeural",
        "female": "es-ES-ElviraNeural",
    },
    "fr-FR": {
        "male": "fr-FR-HenriNeural",
        "female": "fr-FR-DeniseNeural",
    },
    "de-DE": {
        "male": "de-DE-ConradNeural",
        "female": "de-DE-KatjaNeural",
    },
    "ja-JP": {
        "male": "ja-JP-KeitaNeural",
        "female": "ja-JP-NanamiNeural",
    },
    "zh-CN": {
        "male": "zh-CN-YunxiNeural",
        "female": "zh-CN-XiaoxiaoNeural",
    },
    "ar-SA": {
        "male": "ar-SA-HamedNeural",
        "female": "ar-SA-ZariyahNeural",
    },
}


def detect_language(text: str) -> Optional[str]:
    try:
        from langdetect import detect
        lang = detect(text or "")
        mapping = {
            "en": "en-US", "hi": "hi-IN", "es": "es-ES", "fr": "fr-FR",
            "de": "de-DE", "ja": "ja-JP", "zh-cn": "zh-CN", "zh-tw": "zh-CN",
            "ar": "ar-SA", "bn": "en-IN", "ur": "en-IN", "ta": "en-IN",
            "te": "en-IN", "mr": "en-IN", "gu": "en-IN",
        }
        return mapping.get(lang, "en-US")
    except Exception as e:
        logger.debug(f"[Multilingual] langdetect failed: {e}")
        return None


def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> str:
    try:
        import requests
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": f"{source_lang}|{target_lang}"}
        r = requests.get(url, params=params, timeout=8)
        if r.status_code == 200:
            d = r.json()
            return d.get("responseData", {}).get("translatedText", text)
    except Exception as e:
        logger.debug(f"[Multilingual] translate failed: {e}")
    return text


async def edge_tts_speak_async(text: str, voice: str = "en-US-ChristopherNeural", rate: str = "+0%") -> Optional[bytes]:
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        if chunks:
            return b"".join(chunks)
    except Exception as e:
        logger.warning(f"[Multilingual] edge-tts failed: {e}")
    return None


def edge_tts_speak_sync(text: str, voice: str = "en-US-ChristopherNeural", rate: str = "+0%", play: bool = True) -> Optional[str]:
    try:
        audio_bytes = asyncio.run(edge_tts_speak_async(text, voice=voice, rate=rate))
        if not audio_bytes:
            return None
        tmp = Path(tempfile.gettempdir()) / f"jarvis_tts_{abs(hash(text)) % 10000000}.mp3"
        tmp.write_bytes(audio_bytes)
        if play:
            try:
                import platform
                p = platform.system()
                if p == "Windows":
                    import subprocess
                    subprocess.Popen(
                        ["cmd", "/c", "start", "/min", "wmplayer", str(tmp)],
                        creationflags=0x08000000 if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
                    )
                elif p == "Darwin":
                    import subprocess
                    subprocess.Popen(["afplay", str(tmp)])
                else:
                    import subprocess
                    subprocess.Popen(["mpg123", "-q", str(tmp)])
            except Exception as e:
                logger.debug(f"[Multilingual] play failed: {e}")
                return None
        return str(tmp)
    except Exception as e:
        logger.warning(f"[Multilingual] edge-tts sync error: {e}")
        return None


def get_voice_for_locale(locale: str, gender: str = "neutral") -> str:
    group = _EDGE_VOICES.get(locale)
    if not group:
        short = locale.split("-")[0]
        for k, v in _EDGE_VOICES.items():
            if k.startswith(short):
                group = v
                break
    if not group:
        return "en-US-ChristopherNeural"
    return group.get(gender) or group.get("neutral") or list(group.values())[0]


def list_available_voices() -> Dict[str, Any]:
    return _EDGE_VOICES

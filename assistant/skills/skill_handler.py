import re
import json
import math
import random
import datetime
from typing import Optional, Dict, Any, List
from ..skills.reminder_scheduler import ReminderScheduler
from ..utils.logger import logger


class SkillHandler:
    def __init__(self, reminder_scheduler: Optional[ReminderScheduler] = None):
        self.reminders: List[Dict[str, Any]] = []
        self._jokes = self._load_jokes()
        self.reminder_scheduler = reminder_scheduler

    def bind_reminder_scheduler(self, scheduler: ReminderScheduler):
        self.reminder_scheduler = scheduler

    @staticmethod
    def _load_jokes() -> List[str]:
        return [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "Why did the Python developer go broke? Because he used up all his cache.",
            "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
            "Why do Java developers wear glasses? Because they don't C#.",
            "There are 10 types of people in the world: those who understand binary and those who don't.",
            "Why did the developer go broke? Too many cache misses.",
            "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
            "Why don't scientists trust atoms? Because they make up everything.",
            "Parallel lines have so much in common. It's a shame they'll never meet.",
            "Why did the scarecrow win an award? Because he was outstanding in his field.",
            "I told my computer I needed a break, and now it won't stop sending me KitKat ads.",
            "Why do programmers hate nature? It has too many bugs.",
            "Why do ML researchers confuse Halloween and Christmas? Because Oct 31 = Dec 25.",
            "There are only two hard problems in computer science: cache invalidation, naming things, and off-by-one errors.",
            "I would tell you a UDP joke, but you might not get it.",
            "Why do programmers prefer iOS development? Because in iOS, there's no Java to catch you.",
        ]

    def handle(self, intent: str, text: str, context: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        handlers = {
            "time": self._handle_time,
            "date": self._handle_date,
            "weather": self._handle_weather,
            "calculator": self._handle_calculator,
            "reminder": self._handle_reminder,
            "show_reminders": self._handle_show_reminders,
            "joke": self._handle_joke,
            "name": self._handle_name,
            "how_are_you": self._handle_how_are_you,
            "greeting": self._handle_generic,
            "farewell": self._handle_generic,
            "thanks": self._handle_generic,
            "email": self._handle_email,
            "search": self._handle_search,
            "news": self._handle_news,
            "music": self._handle_music,
            "translate": self._handle_translate,
            "language": self._handle_language,
            "whatsapp": self._handle_whatsapp,
            "switch_voice": self._handle_switch_voice,
            "unknown": self._handle_unknown,
        }

        math_hint = re.search(
            r"(?:calculate|compute|solve|evaluate|what\s+is)\b.*\d+.*[+\-*/%^()]|^\s*\d+\s*[+\-*/]\s*\d+|\d+\s*(?:times|plus|minus|divided|multiply|percent|squared|cubed)\b",
            text, re.IGNORECASE)
        if math_hint or self._extract_math_expression(text):
            return self._handle_calculator(text, context)

        if re.search(r"\b(translate|translation)\b", text, re.IGNORECASE):
            return self._handle_translate(text, context)
        if re.search(r"\b(remind|reminder)\b", text, re.IGNORECASE):
            return self._handle_reminder(text, context)
        if re.search(r"\b(whatsapp|send message)\b", text, re.IGNORECASE):
            return self._handle_whatsapp(text, context)
        if re.search(r"\b(switch.*voice|change.*voice|female|male voice)\b", text, re.IGNORECASE):
            return self._handle_switch_voice(text, context)

        handler = handlers.get(intent)
        if handler:
            return handler(text, context)
        return self._handle_unknown(text, context)

    def _handle_generic(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        responses = context.get("responses", []) if context else []
        if responses:
            return {"text": random.choice(responses), "intent": "generic_response"}
        return {"text": "I'm here to help!", "intent": "generic_response"}

    def _handle_time(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        hour = now.hour
        if 5 <= hour < 12:
            greeting = "Good morning"
        elif 12 <= hour < 17:
            greeting = "Good afternoon"
        elif 17 <= hour < 21:
            greeting = "Good evening"
        else:
            greeting = "It's nighttime"
        return {
            "text": f"{greeting}. The current time is {time_str}.",
            "intent": "time",
            "data": {"time": time_str, "hour": hour, "minute": now.minute}
        }

    def _handle_date(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        return {
            "text": f"Today is {date_str}.",
            "intent": "date",
            "data": {
                "date": date_str,
                "day_of_week": now.strftime("%A"),
                "month": now.strftime("%B"),
                "day": now.day,
                "year": now.year
            }
        }

    def _handle_weather(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        city = self._extract_city(text)
        try:
            import requests
            url = "https://wttr.in/{city}?format=j1"
            r = requests.get(url.format(city=city or "NewYork"), timeout=5)
            if r.status_code == 200:
                data = r.json()
                current = data.get("current_condition", [{}])[0]
                temp_c = current.get("temp_C", "N/A")
                temp_f = current.get("temp_F", "N/A")
                desc = current.get("weatherDesc", [{}])[0].get("value", "")
                humidity = current.get("humidity", "N/A")
                wind_speed = current.get("windspeedKmph", "N/A")
                return {
                    "text": f"In {city or 'your area'}, it's currently {temp_c}°C ({temp_f}°F) with {desc.lower()}. Humidity is {humidity}% and wind speed is {wind_speed} km/h.",
                    "intent": "weather",
                    "data": {
                        "city": city,
                        "temp_c": temp_c,
                        "temp_f": temp_f,
                        "description": desc,
                        "humidity": humidity,
                        "wind_speed": wind_speed
                    }
                }
        except Exception as e:
            logger.debug(f"[Weather] API error: {e}")
        return {
            "text": f"I couldn't fetch live weather data for {city or 'your area'}, but I can tell you it's always a great day to code in Python! (Make sure you're connected to the internet for live updates.)",
            "intent": "weather",
            "data": {"city": city, "error": True}
        }

    @staticmethod
    def _extract_city(text: str) -> Optional[str]:
        m = re.search(r"(?:in|for|at)\s+([A-Za-z\s]+?)(?:\s*today|\s*tomorrow|\s*now|\.|$)", text, re.IGNORECASE)
        if m:
            return m.group(1).strip().title()
        return None

    def _handle_calculator(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        expression = self._extract_math_expression(text)
        if not expression:
            return {"text": "I can help you calculate! Try asking: 'what is 15 percent of 200?' or 'solve 12 * 5 + 3'", "intent": "calculator", "error": True}
        try:
            safe_dict = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sqrt": math.sqrt, "pow": math.pow, "log": math.log,
                "log10": math.log10, "sin": math.sin, "cos": math.cos,
                "tan": math.tan, "pi": math.pi, "e": math.e,
                "factorial": math.factorial, "ceil": math.ceil, "floor": math.floor
            }
            for name in dir(math):
                if not name.startswith("_"):
                    safe_dict[name] = getattr(math, name)
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return {
                "text": f"The result of {expression} is {result}.",
                "intent": "calculator",
                "data": {"expression": expression, "result": result}
            }
        except Exception as e:
            return {
                "text": f"Sorry, I couldn't compute that expression: '{expression}'. Please try a simpler one.",
                "intent": "calculator",
                "error": True
            }

    def _extract_math_expression(self, text: str) -> Optional[str]:
        expr = text.lower()
        filler_words = [
            r"\bthe\b", r"\bresult\b", r"\banswer\b", r"\bvalue\b",
            r"\btell\b", r"\bme\b", r"\bshow\b", r"\bgive\b", r"\bcan you\b",
            r"\bfind\b", r"\bget\b", r"\bwork\s+out\b", r"\bfigure\s+out\b",
            r"\bplease\b", r"\bthanks?\b", r"\bokay\b", r"\bok\b", r"\bfor\b",
        ]
        for w in filler_words:
            expr = re.sub(w, " ", expr, flags=re.IGNORECASE)
        word_replacements = {
            r"\bplus\b": "+", r"\bminus\b": "-", r"\btimes\b": "*",
            r"\bdivided by\b": "/", r"\bdivided\s+by\b": "/",
            r"\bmultiply by\b": "*", r"\bmultiplied by\b": "*",
            r"\bsubtract\b": "-", r"\badd\b": "+", r"\bwhat is\b": "",
            r"\bwhats\b": "", r"\bcalculate\b": "", r"\bcompute\b": "", r"\bsolve\b": "",
            r"\bevaluate\b": "", r"\bof\b": "*", r"\bpercent\b": "/100",
            r"\bpercentage\b": "/100", r"\bsquared\b": "**2", r"\bcubed\b": "**3",
        }
        for pattern, repl in word_replacements.items():
            expr = re.sub(pattern, repl, expr, flags=re.IGNORECASE)
        expr = re.sub(r"[^0-9+\-*/().%^ a-zA-Z]", "", expr)
        expr = re.sub(r"\s+", " ", expr).strip()
        expr = expr.replace("^", "**")
        if len(expr) < 2:
            return None
        allowed_pattern = r"^[\d+\-*/().%\sa-zA-Z]+$"
        if re.match(allowed_pattern, expr):
            return expr if re.search(r"[+\-*/()**%]", expr) or any(k in expr for k in ["sqrt", "sin", "cos", "tan", "log", "abs", "round"]) else None
        return None

    def _handle_reminder(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        reminder_text = self._extract_reminder_text(text)
        if not reminder_text:
            return {"text": "Sure! What would you like me to remind you about? Say something like 'remind me to call mom tomorrow' or 'remind me in 30 minutes to take a break'.", "intent": "reminder", "needs_more": True}
        if self.reminder_scheduler is not None:
            try:
                created = self.reminder_scheduler.parse_and_add(reminder_text, text)
                when = created.get("fire_at") or created.get("recurrence") or "soon"
                return {
                    "text": f"Got it! I've scheduled a persistent reminder: '{reminder_text}'. When: {when}. I'll notify you loudly when it's time.",
                    "intent": "reminder",
                    "data": {"reminder": created, "scheduler": True}
                }
            except Exception as e:
                logger.warning(f"[SkillHandler] Scheduler add failed: {e}")
        reminder = {
            "id": len(self.reminders) + 1,
            "text": reminder_text,
            "created_at": datetime.datetime.now().isoformat(),
            "completed": False
        }
        self.reminders.append(reminder)
        return {
            "text": f"Got it! I've added a reminder: '{reminder_text}'. You have {len(self.reminders)} reminder(s) total.",
            "intent": "reminder",
            "data": {"reminder": reminder, "total": len(self.reminders)}
        }

    @staticmethod
    def _extract_reminder_text(text: str) -> Optional[str]:
        patterns = [
            r"(?:remind me to|set a? reminder to|don't let me forget to|note that|remember to)\s+(.+)",
            r"(?:remind me about|set a? reminder about|remember this)\s*(?:that)?\s*[:]?\s*(.+)",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip().rstrip(".!?")
        return None

    def _handle_show_reminders(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        if self.reminder_scheduler is not None:
            items = self.reminder_scheduler.list_reminders()
            if not items:
                return {"text": "You don't have any scheduled reminders yet. Say something like 'remind me in 30 minutes to take a break' to add one!", "intent": "show_reminders"}
            lines = []
            for i, r in enumerate(items):
                when = r.get("fire_at") or r.get("recurrence") or "scheduled"
                lines.append(f"{i+1}. [{when}] {r.get('text','')}")
            response = f"Here are your {len(items)} scheduled reminders:\n" + "\n".join(lines)
            return {"text": response, "intent": "show_reminders", "data": {"reminders": items, "count": len(items)}}
        if not self.reminders:
            return {"text": "You don't have any reminders yet. Say something like 'remind me to buy groceries' to add one!", "intent": "show_reminders"}
        lines = [f"{i+1}. [{('Done' if r['completed'] else 'Pending')}] {r['text']}" for i, r in enumerate(self.reminders)]
        response = "Here are your reminders:\n" + "\n".join(lines)
        return {"text": response, "intent": "show_reminders", "data": {"reminders": list(self.reminders), "count": len(self.reminders)}}

    def _handle_joke(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        joke = random.choice(self._jokes)
        return {"text": f"Here's one for you: {joke}", "intent": "joke", "data": {"joke": joke}}

    def _handle_name(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        responses = context.get("responses", []) if context else []
        if responses:
            return {"text": random.choice(responses), "intent": "name"}
        return {"text": "I'm Jarvis, your personal AI assistant built with Python and Machine Learning.", "intent": "name"}

    def _handle_how_are_you(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        responses = context.get("responses", []) if context else []
        if responses:
            return {"text": random.choice(responses), "intent": "how_are_you"}
        return {"text": "I'm doing great! Thanks for asking. All systems nominal and ready for your commands.", "intent": "how_are_you"}

    def _handle_email(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        return {"text": "I can help you compose an email! Tell me the recipient and what you'd like the message to say. (Note: For security, I'll draft the message but won't send it without your explicit permission.)", "intent": "email", "data": {"status": "awaiting_content"}}

    def _handle_search(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        query = re.sub(r"^(search for|look up|find information about|google|search the web|what is|who is|tell me about|explain)\s+", "", text, flags=re.IGNORECASE).strip()
        if not query:
            return {"text": "What would you like me to look up for you?", "intent": "search", "needs_more": True}
        try:
            import requests
            from bs4 import BeautifulSoup
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(query)}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                extract = data.get("extract", "")
                if extract:
                    summary = extract[:500] + ("..." if len(extract) > 500 else "")
                    return {"text": f"Here's what I found about {query}: {summary}", "intent": "search", "data": {"query": query, "source": "wikipedia"}}
        except Exception:
            pass
        return {"text": f"I'd love to search for '{query}' for you. While I can't browse the entire web in detail right now, you can try opening https://www.google.com/search?q={query.replace(' ', '+')} in your browser for full results.", "intent": "search", "data": {"query": query}}

    def _handle_news(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        return {"text": "For the latest news, I recommend checking news.google.com or your favorite news source. If you'd like, I can search for specific topics for you!", "intent": "news"}

    def _handle_music(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        return {"text": "🎵 Let's get some vibes going! You can open Spotify, YouTube Music, or your favorite music player. What genre or artist are you in the mood for?", "intent": "music"}

    def _handle_translate(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        from ..voice.multilingual import translate_text, detect_language
        source = "auto"
        target = "es"
        content = ""
        m = re.search(r'translate\s+["\']?(.+?)["\']?\s+(?:in)?to\s+([a-zA-Z]+)', text, re.IGNORECASE)
        if m:
            content = m.group(1).strip()
            lang_map = {
                "spanish": "es", "french": "fr", "german": "de", "hindi": "hi", "chinese": "zh-CN",
                "japanese": "ja", "arabic": "ar", "italian": "it", "portuguese": "pt", "russian": "ru",
                "korean": "ko", "tamil": "ta", "telugu": "te", "bengali": "bn", "urdu": "ur",
                "marathi": "mr", "gujarati": "gu", "punjabi": "pa", "es": "es", "fr": "fr", "de": "de",
            }
            target = lang_map.get(m.group(2).lower(), m.group(2)[:2].lower())
        if not content:
            m2 = re.search(r'translate\s+["\'](.+?)["\']', text)
            if m2:
                content = m2.group(1)
        if not content:
            return {"text": "Sure! Ask something like: 'translate hello world to Spanish' or 'translate good morning to Hindi'.", "intent": "translate", "needs_more": True}
        detected = detect_language(content) or source
        result = translate_text(content, target, source)
        return {
            "text": f"Translation (from {detected} to {target}): {result}",
            "intent": "translate",
            "data": {"from": detected, "to": target, "original": content, "translated": result}
        }

    def _handle_language(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        return {"text": "I support 50+ languages via Edge TTS voices. Ask me to: 'switch to female voice', 'translate hello to French', or try my multilingual speech in 10+ locales.", "intent": "language"}

    def _handle_whatsapp(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        phone_match = re.search(r"(?:to\s+)?(?:\+?\d[\d\s\-]{7,}\d)", text)
        msg_match = re.search(r'(?:message|send|whatsapp)\s*(?:.+?)?(?:that|saying|text)[:]?\s*["\']?(.+?)["\']?$', text, re.IGNORECASE)
        phone = phone_match.group(0).strip() if phone_match else None
        message = msg_match.group(1).strip('" \'') if msg_match else None
        if not phone or not message:
            return {
                "text": "I can send WhatsApp messages via pywhatkit! Use: 'send WhatsApp +911234567890 saying Hi there' — I'll open WhatsApp Web and send it for you.",
                "intent": "whatsapp",
                "needs_more": True,
            }
        try:
            import pywhatkit
            now = datetime.datetime.now()
            pywhatkit.sendwhatmsg(
                phone.replace(" ", ""),
                message,
                time_hour=now.hour,
                time_min=(now.minute + 2) % 60,
                wait_time=15,
                tab_close=True,
            )
            return {"text": f"WhatsApp message queued for {phone}: '{message[:60]}...'", "intent": "whatsapp", "data": {"phone": phone, "message": message}}
        except ImportError:
            return {"text": "pywhatkit is in your requirements — try pip install -r requirements.txt to enable WhatsApp sending.", "intent": "whatsapp", "error": True}
        except Exception as e:
            return {"text": f"Couldn't send WhatsApp message: {e}. Please ensure WhatsApp Web is logged in on your default browser.", "intent": "whatsapp", "error": True}

    def _handle_switch_voice(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        from ..voice.multilingual import list_available_voices, get_voice_for_locale
        low = text.lower()
        gender = "neutral"
        locale = "en-US"
        if "female" in low or "woman" in low or "girl" in low:
            gender = "female"
        elif "male" in low or "man" in low or "guy" in low:
            gender = "male"
        locale_map = {
            "hindi": "hi-IN", "indian": "en-IN", "british": "en-GB", "uk": "en-GB",
            "spanish": "es-ES", "french": "fr-FR", "german": "de-DE", "japanese": "ja-JP",
            "chinese": "zh-CN", "arabic": "ar-SA", "american": "en-US", "us": "en-US",
        }
        for k, v in locale_map.items():
            if k in low:
                locale = v
                break
        voice = get_voice_for_locale(locale, gender)
        available = list_available_voices()
        return {
            "text": f"Voice set: {voice} (locale={locale}, gender={gender}). I can switch to {len(available)} locale groups; use Edge TTS engine for 50+ neural voices.",
            "intent": "switch_voice",
            "data": {"voice": voice, "locale": locale, "gender": gender, "available_groups": sorted(available.keys())}
        }

    def _handle_unknown(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        fallback = [
            "Hmm, I'm not sure I understood that. Could you rephrase it?",
            "I don't have a specific skill for that yet, but I'm always learning! Can you try saying it differently?",
            "Interesting! Could you be more specific? I can help with time, date, weather, calculations, reminders, jokes, and more.",
            "I didn't quite catch that. Try asking about the weather, setting a reminder, or solving a math problem!"
        ]
        return {"text": random.choice(fallback), "intent": "unknown", "error": True}

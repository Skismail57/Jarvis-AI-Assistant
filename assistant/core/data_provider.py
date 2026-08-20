import os
import re
import json
import urllib.parse
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    snippet: str
    url: str


@dataclass
class MapResult:
    name: str
    address: str
    latitude: Optional[float]
    longitude: Optional[float]


class DataProvider:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.country_db_path = os.path.join(self.base_dir, "data", "countries.json")
        self._ensure_country_db()

    def _ensure_country_db(self):
        if not os.path.exists(self.country_db_path):
            self._build_country_db()

    def _build_country_db(self):
        minimal = [
            {"name": "United States", "cca2": "US", "capital": "Washington, D.C.", "region": "Americas",
             "population": 331000000, "timezones": ["UTC-04:00", "UTC-05:00", "UTC-06:00", "UTC-07:00", "UTC-08:00", "UTC-09:00", "UTC-10:00"],
             "currency": {"code": "USD", "name": "United States dollar"}, "languages": {"eng": "English"}, "flag": "🇺🇸"},
            {"name": "India", "cca2": "IN", "capital": "New Delhi", "region": "Asia",
             "population": 1408000000, "timezones": ["UTC+05:30"],
             "currency": {"code": "INR", "name": "Indian rupee"}, "languages": {"eng": "English", "hin": "Hindi"}, "flag": "🇮🇳"},
            {"name": "United Kingdom", "cca2": "GB", "capital": "London", "region": "Europe",
             "population": 67220000, "timezones": ["UTC+00:00"],
             "currency": {"code": "GBP", "name": "Pound sterling"}, "languages": {"eng": "English"}, "flag": "🇬🇧"},
            {"name": "Canada", "cca2": "CA", "capital": "Ottawa", "region": "Americas",
             "population": 38010000, "timezones": ["UTC-03:30", "UTC-04:00", "UTC-05:00", "UTC-06:00", "UTC-07:00", "UTC-08:00"],
             "currency": {"code": "CAD", "name": "Canadian dollar"}, "languages": {"eng": "English", "fra": "French"}, "flag": "🇨🇦"},
            {"name": "Australia", "cca2": "AU", "capital": "Canberra", "region": "Oceania",
             "population": 25690000, "timezones": ["UTC+08:00", "UTC+08:45", "UTC+09:30", "UTC+10:00", "UTC+10:30", "UTC+11:00"],
             "currency": {"code": "AUD", "name": "Australian dollar"}, "languages": {"eng": "English"}, "flag": "🇦🇺"},
            {"name": "Germany", "cca2": "DE", "capital": "Berlin", "region": "Europe",
             "population": 83240000, "timezones": ["UTC+01:00"],
             "currency": {"code": "EUR", "name": "Euro"}, "languages": {"deu": "German"}, "flag": "🇩🇪"},
            {"name": "France", "cca2": "FR", "capital": "Paris", "region": "Europe",
             "population": 67390000, "timezones": ["UTC+01:00"],
             "currency": {"code": "EUR", "name": "Euro"}, "languages": {"fra": "French"}, "flag": "🇫🇷"},
            {"name": "Japan", "cca2": "JP", "capital": "Tokyo", "region": "Asia",
             "population": 125800000, "timezones": ["UTC+09:00"],
             "currency": {"code": "JPY", "name": "Japanese yen"}, "languages": {"jpn": "Japanese"}, "flag": "🇯🇵"},
            {"name": "China", "cca2": "CN", "capital": "Beijing", "region": "Asia",
             "population": 1412000000, "timezones": ["UTC+08:00"],
             "currency": {"code": "CNY", "name": "Renminbi"}, "languages": {"zho": "Chinese"}, "flag": "🇨🇳"},
            {"name": "Brazil", "cca2": "BR", "capital": "Brasília", "region": "Americas",
             "population": 212600000, "timezones": ["UTC-02:00", "UTC-03:00", "UTC-04:00", "UTC-05:00"],
             "currency": {"code": "BRL", "name": "Brazilian real"}, "languages": {"por": "Portuguese"}, "flag": "🇧🇷"},
            {"name": "Russia", "cca2": "RU", "capital": "Moscow", "region": "Europe",
             "population": 144100000, "timezones": ["UTC+02:00", "UTC+03:00", "UTC+04:00", "UTC+05:00", "UTC+06:00", "UTC+07:00", "UTC+08:00", "UTC+09:00", "UTC+10:00", "UTC+11:00", "UTC+12:00"],
             "currency": {"code": "RUB", "name": "Russian ruble"}, "languages": {"rus": "Russian"}, "flag": "🇷🇺"},
            {"name": "South Africa", "cca2": "ZA", "capital": "Pretoria", "region": "Africa",
             "population": 59310000, "timezones": ["UTC+02:00"],
             "currency": {"code": "ZAR", "name": "South African rand"}, "languages": {"eng": "English", "zul": "Zulu"}, "flag": "🇿🇦"},
            {"name": "Mexico", "cca2": "MX", "capital": "Mexico City", "region": "Americas",
             "population": 126000000, "timezones": ["UTC-05:00", "UTC-06:00", "UTC-07:00", "UTC-08:00"],
             "currency": {"code": "MXN", "name": "Mexican peso"}, "languages": {"spa": "Spanish"}, "flag": "🇲🇽"},
            {"name": "Italy", "cca2": "IT", "capital": "Rome", "region": "Europe",
             "population": 59550000, "timezones": ["UTC+01:00"],
             "currency": {"code": "EUR", "name": "Euro"}, "languages": {"ita": "Italian"}, "flag": "🇮🇹"},
            {"name": "Spain", "cca2": "ES", "capital": "Madrid", "region": "Europe",
             "population": 47350000, "timezones": ["UTC+01:00"],
             "currency": {"code": "EUR", "name": "Euro"}, "languages": {"spa": "Spanish"}, "flag": "🇪🇸"},
            {"name": "South Korea", "cca2": "KR", "capital": "Seoul", "region": "Asia",
             "population": 51780000, "timezones": ["UTC+09:00"],
             "currency": {"code": "KRW", "name": "South Korean won"}, "languages": {"kor": "Korean"}, "flag": "🇰🇷"},
            {"name": "Saudi Arabia", "cca2": "SA", "capital": "Riyadh", "region": "Asia",
             "population": 34810000, "timezones": ["UTC+03:00"],
             "currency": {"code": "SAR", "name": "Saudi riyal"}, "languages": {"ara": "Arabic"}, "flag": "🇸🇦"},
            {"name": "UAE", "cca2": "AE", "capital": "Abu Dhabi", "region": "Asia",
             "population": 9890000, "timezones": ["UTC+04:00"],
             "currency": {"code": "AED", "name": "UAE dirham"}, "languages": {"ara": "Arabic"}, "flag": "🇦🇪"},
            {"name": "Singapore", "cca2": "SG", "capital": "Singapore", "region": "Asia",
             "population": 5850000, "timezones": ["UTC+08:00"],
             "currency": {"code": "SGD", "name": "Singapore dollar"}, "languages": {"eng": "English", "zho": "Chinese", "msa": "Malay", "tam": "Tamil"}, "flag": "🇸🇬"},
            {"name": "Pakistan", "cca2": "PK", "capital": "Islamabad", "region": "Asia",
             "population": 220900000, "timezones": ["UTC+05:00"],
             "currency": {"code": "PKR", "name": "Pakistani rupee"}, "languages": {"urd": "Urdu", "eng": "English"}, "flag": "🇵🇰"},
            {"name": "Bangladesh", "cca2": "BD", "capital": "Dhaka", "region": "Asia",
             "population": 164700000, "timezones": ["UTC+06:00"],
             "currency": {"code": "BDT", "name": "Taka"}, "languages": {"ben": "Bengali"}, "flag": "🇧🇩"},
            {"name": "Nigeria", "cca2": "NG", "capital": "Abuja", "region": "Africa",
             "population": 206100000, "timezones": ["UTC+01:00"],
             "currency": {"code": "NGN", "name": "Nigerian naira"}, "languages": {"eng": "English"}, "flag": "🇳🇬"},
            {"name": "Turkey", "cca2": "TR", "capital": "Ankara", "region": "Asia",
             "population": 84340000, "timezones": ["UTC+03:00"],
             "currency": {"code": "TRY", "name": "Turkish lira"}, "languages": {"tur": "Turkish"}, "flag": "🇹🇷"},
            {"name": "New Zealand", "cca2": "NZ", "capital": "Wellington", "region": "Oceania",
             "population": 5084000, "timezones": ["UTC+12:00"],
             "currency": {"code": "NZD", "name": "New Zealand dollar"}, "languages": {"eng": "English"}, "flag": "🇳🇿"},
        ]
        os.makedirs(os.path.dirname(self.country_db_path), exist_ok=True)
        with open(self.country_db_path, "w", encoding="utf-8") as f:
            json.dump(minimal, f, indent=2, ensure_ascii=False)

    def web_search(self, query: str, max_results: int = 5, time_limit: str = "y") -> List[SearchResult]:
        try:
            from duckduckgo_search import DDGS
            out: List[SearchResult] = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results, timelimit=time_limit):
                    out.append(SearchResult(title=r.get("title", ""), snippet=r.get("body", ""), url=r.get("href", "")))
            return out
        except Exception as e:
            try:
                import requests
                from bs4 import BeautifulSoup
                url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(url, headers=headers, timeout=8)
                soup = BeautifulSoup(resp.text, "html.parser")
                out = []
                for r in soup.select(".result")[:max_results]:
                    a = r.select_one(".result__a")
                    s = r.select_one(".result__snippet")
                    if a:
                        out.append(SearchResult(
                            title=a.get_text(strip=True),
                            snippet=s.get_text(strip=True) if s else "",
                            url=a.get("href", "")
                        ))
                return out
            except Exception as e2:
                raise RuntimeError(f"Web search unavailable: {e} / {e2}")

    def maps_search(self, query: str) -> List[MapResult]:
        try:
            import requests
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=5&addressdetails=1"
            headers = {"User-Agent": "JARVIS-AI-Assistant/1.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()
            results: List[MapResult] = []
            for item in data:
                addr = item.get("display_name", "")
                results.append(MapResult(
                    name=item.get("name") or addr.split(",")[0],
                    address=addr,
                    latitude=float(item["lat"]) if item.get("lat") else None,
                    longitude=float(item["lon"]) if item.get("lon") else None,
                ))
            return results
        except Exception as e:
            raise RuntimeError(f"Maps search unavailable: {e}")

    def get_directions_url(self, origin: str, destination: str) -> str:
        return f"https://www.google.com/maps/dir/{urllib.parse.quote(origin)}/{urllib.parse.quote(destination)}"

    def weather(self, location: str) -> Dict[str, Any]:
        import requests
        try:
            url = f"https://wttr.in/{urllib.parse.quote(location or 'New York')}?format=j1"
            r = requests.get(url, timeout=8, headers={"User-Agent": "curl/8.0"})
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}")
            d = r.json()
            cur = d.get("current_condition", [{}])[0]
            astronomy = d.get("weather", [{}])[0].get("astronomy", [{}])[0]
            return {
                "location": location,
                "temp_c": cur.get("temp_C"),
                "temp_f": cur.get("temp_F"),
                "feelslike_c": cur.get("FeelsLikeC"),
                "feelslike_f": cur.get("FeelsLikeF"),
                "condition": cur.get("weatherDesc", [{}])[0].get("value", ""),
                "humidity": cur.get("humidity"),
                "windspeed_kmh": cur.get("windspeedKmph"),
                "winddir": cur.get("winddir16Point"),
                "visibility_km": cur.get("visibility"),
                "uv_index": cur.get("uvIndex"),
                "pressure": cur.get("pressure"),
                "sunrise": astronomy.get("sunrise"),
                "sunset": astronomy.get("sunset"),
                "moon_phase": astronomy.get("moon_phase"),
            }
        except Exception as e:
            raise RuntimeError(f"Weather API error: {e}")

    def get_country(self, name: str) -> Optional[Dict[str, Any]]:
        with open(self.country_db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
        q = name.strip().lower()
        for c in db:
            if c["name"].lower() == q or c["cca2"].lower() == q:
                return c
        for c in db:
            if q in c["name"].lower():
                return c
        return None

    def list_countries(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        with open(self.country_db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
        if region:
            rl = region.lower()
            return [c for c in db if rl in c.get("region", "").lower()]
        return db

    def currency_convert(self, amount: float, from_code: str, to_code: str) -> Dict[str, Any]:
        import requests
        try:
            f, t = from_code.upper(), to_code.upper()
            url = f"https://open.er-api.com/v6/latest/{f}"
            r = requests.get(url, timeout=8)
            data = r.json()
            if data.get("result") != "success":
                raise RuntimeError("rates API failed")
            rate = data["rates"].get(t)
            if rate is None:
                raise RuntimeError(f"Unknown target currency: {t}")
            converted = round(amount * rate, 4)
            return {
                "from": f, "to": t, "amount": amount,
                "rate": rate, "converted": converted,
                "last_updated": data.get("time_last_update_utc")
            }
        except Exception as e:
            import math
            manual = {"USD-EUR": 0.92, "USD-GBP": 0.79, "USD-INR": 83.5, "USD-JPY": 158.0, "USD-CAD": 1.36,
                      "USD-AUD": 1.52, "EUR-USD": 1.09, "GBP-USD": 1.27, "INR-USD": 0.012, "USD-CNY": 7.25,
                      "USD-BRL": 5.5, "USD-MXN": 17.1}
            pair = f"{from_code.upper()}-{to_code.upper()}"
            if pair in manual:
                r = manual[pair]
                return {"from": from_code.upper(), "to": to_code.upper(), "amount": amount,
                        "rate": r, "converted": round(amount * r, 4),
                        "last_updated": "offline approximate rate", "note": "approximate offline rate"}
            raise RuntimeError(f"Currency conversion error: {e}")

    def get_time_in(self, timezone_or_city: str) -> Dict[str, Any]:
        from datetime import datetime
        try:
            import requests
            url = f"http://worldtimeapi.org/api/timezone/{urllib.parse.quote(timezone_or_city)}"
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                data = r.json()
                dt = datetime.fromisoformat(data["datetime"])
                return {
                    "query": timezone_or_city,
                    "time": dt.strftime("%I:%M %p"),
                    "date": dt.strftime("%A, %B %d, %Y"),
                    "timezone": data.get("timezone"),
                    "utc_offset": data.get("utc_offset"),
                    "unixtime": data.get("unixtime"),
                }
        except Exception:
            pass
        try:
            from datetime import timezone, timedelta
            import re
            m = re.match(r"UTC([+-])(\d{1,2}):?(\d{2})?", timezone_or_city.upper())
            if m:
                sign = 1 if m.group(1) == "+" else -1
                hh = int(m.group(2))
                mm = int(m.group(3) or 0)
                tz = timezone(timedelta(hours=sign * hh, minutes=sign * mm))
                dt = datetime.now(tz)
                return {
                    "query": timezone_or_city,
                    "time": dt.strftime("%I:%M %p"),
                    "date": dt.strftime("%A, %B %d, %Y"),
                    "timezone": f"UTC{m.group(1)}{hh:02d}:{mm:02d}",
                    "utc_offset": f"{m.group(1)}{hh:02d}{mm:02d}",
                }
        except Exception:
            pass
        return {
            "query": timezone_or_city,
            "time": datetime.now().strftime("%I:%M %p"),
            "date": datetime.now().strftime("%A, %B %d, %Y"),
            "timezone": "local",
            "note": "fallback to local time",
        }

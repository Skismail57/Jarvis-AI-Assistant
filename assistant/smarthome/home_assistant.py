import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

from ..utils.logger import logger
from ..config import settings, DATA_DIR


CAMERAS_DIR = Path(DATA_DIR) / "cameras"
CAMERAS_DIR.mkdir(parents=True, exist_ok=True)


class HomeAssistantBridge:
    def __init__(self, base_url: Optional[str] = None, access_token: Optional[str] = None):
        self.base_url = (base_url or os.getenv("HOME_ASSISTANT_URL") or "").rstrip("/")
        self.access_token = access_token or os.getenv("HOME_ASSISTANT_TOKEN") or ""
        self._available = None

    @property
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _configured(self) -> bool:
        return bool(self.base_url and self.access_token)

    def is_available(self) -> bool:
        if not self._configured():
            logger.warning("[HomeAssistant] Not configured (missing URL or token).")
            self._available = False
            return False
        try:
            import requests
            url = urljoin(self.base_url + "/", "api/")
            r = requests.get(url, headers=self._headers, timeout=5)
            ok = r.status_code == 200
            self._available = ok
            if not ok:
                logger.warning(f"[HomeAssistant] /api/ ping failed: HTTP {r.status_code}")
            return ok
        except Exception as e:
            logger.error(f"[HomeAssistant] Availability check failed: {e}")
            self._available = False
            return False

    def list_entities(self, entity_type: str = "light") -> List[Dict[str, Any]]:
        if not self._configured():
            return []
        try:
            import requests
            url = urljoin(self.base_url + "/", "api/states")
            r = requests.get(url, headers=self._headers, timeout=10)
            if r.status_code != 200:
                logger.warning(f"[HomeAssistant] list_entities HTTP {r.status_code}")
                return []
            states = r.json()
            domain = (entity_type or "").lower()
            filtered = []
            for s in states:
                eid = s.get("entity_id", "")
                if domain and "." in eid:
                    if eid.split(".", 1)[0] == domain:
                        filtered.append(s)
                elif not domain:
                    filtered.append(s)
            logger.info(f"[HomeAssistant] Listed {len(filtered)} {domain or 'all'} entities")
            return filtered
        except Exception as e:
            logger.error(f"[HomeAssistant] list_entities error: {e}")
            return []

    def turn_on(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        domain = entity_id.split(".", 1)[0] if "." in entity_id else "light"
        service = "turn_on"
        data = {"entity_id": entity_id}
        if kwargs:
            data.update(kwargs)
        return self.call_service(domain, service, data)

    def turn_off(self, entity_id: str) -> Dict[str, Any]:
        domain = entity_id.split(".", 1)[0] if "." in entity_id else "light"
        service = "turn_off"
        return self.call_service(domain, service, {"entity_id": entity_id})

    def set_state(self, entity_id: str, state: str, attributes: Optional[dict] = None) -> Dict[str, Any]:
        if not self._configured():
            return {"success": False, "error": "Home Assistant not configured."}
        try:
            import requests
            url = urljoin(self.base_url + "/", f"api/states/{entity_id}")
            payload: Dict[str, Any] = {"state": state}
            if attributes:
                payload["attributes"] = attributes
            r = requests.post(url, headers=self._headers, json=payload, timeout=10)
            ok = r.status_code in (200, 201)
            if not ok:
                logger.warning(f"[HomeAssistant] set_state HTTP {r.status_code}: {r.text[:200]}")
            return {"success": ok, "status_code": r.status_code, "response": r.json() if ok else r.text[:500]}
        except Exception as e:
            logger.error(f"[HomeAssistant] set_state error: {e}")
            return {"success": False, "error": str(e)}

    def call_service(self, domain: str, service: str, service_data: Optional[dict] = None) -> Dict[str, Any]:
        if not self._configured():
            return {"success": False, "error": "Home Assistant not configured."}
        try:
            import requests
            url = urljoin(self.base_url + "/", f"api/services/{domain}/{service}")
            r = requests.post(url, headers=self._headers, json=(service_data or {}), timeout=10)
            ok = r.status_code == 200
            if not ok:
                logger.warning(f"[HomeAssistant] call_service {domain}.{service} HTTP {r.status_code}: {r.text[:200]}")
            try:
                body = r.json()
            except Exception:
                body = r.text[:500]
            return {"success": ok, "status_code": r.status_code, "response": body}
        except Exception as e:
            logger.error(f"[HomeAssistant] call_service {domain}.{service} error: {e}")
            return {"success": False, "error": str(e)}

    def get_camera_snapshot(self, entity_id: str, save_path: str) -> Optional[str]:
        if not self._configured():
            logger.warning("[HomeAssistant] get_camera_snapshot: not configured.")
            return None
        try:
            import requests
            url = urljoin(self.base_url + "/", f"api/camera_proxy/{entity_id}")
            r = requests.get(url, headers=self._headers, timeout=15, stream=True)
            if r.status_code != 200:
                logger.warning(f"[HomeAssistant] camera snapshot HTTP {r.status_code}")
                return None
            save_p = Path(save_path)
            save_p.parent.mkdir(parents=True, exist_ok=True)
            with open(save_p, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logger.info(f"[HomeAssistant] Camera snapshot saved to {save_p}")
            return str(save_p)
        except Exception as e:
            logger.error(f"[HomeAssistant] get_camera_snapshot error: {e}")
            return None

    @staticmethod
    def trigger_ifttt_webhook(event: str, api_key: Optional[str] = None,
                              value1: Optional[str] = None, value2: Optional[str] = None,
                              value3: Optional[str] = None) -> bool:
        key = api_key or os.getenv("IFTTT_WEBHOOK_KEY")
        if not key or not event:
            logger.warning("[HomeAssistant] IFTTT trigger skipped: missing key or event.")
            return False
        try:
            import requests
            url = f"https://maker.ifttt.com/trigger/{event}/json/with/key/{key}"
            payload = {}
            if value1 is not None:
                payload["value1"] = value1
            if value2 is not None:
                payload["value2"] = value2
            if value3 is not None:
                payload["value3"] = value3
            r = requests.post(url, json=payload, timeout=10)
            ok = r.status_code == 200
            logger.info(f"[HomeAssistant] IFTTT webhook {event}: {'OK' if ok else 'FAIL'} ({r.status_code})")
            return ok
        except Exception as e:
            logger.error(f"[HomeAssistant] IFTTT webhook error: {e}")
            return False

    @staticmethod
    def trigger_zapier_webhook(url: str, payload: Optional[dict] = None) -> bool:
        if not url:
            logger.warning("[HomeAssistant] Zapier trigger skipped: missing URL.")
            return False
        try:
            import requests
            r = requests.post(url, json=(payload or {}), timeout=10)
            ok = 200 <= r.status_code < 300
            logger.info(f"[HomeAssistant] Zapier webhook: {'OK' if ok else 'FAIL'} ({r.status_code})")
            return ok
        except Exception as e:
            logger.error(f"[HomeAssistant] Zapier webhook error: {e}")
            return False

    def _find_entity(self, room: str, device: str, domain: str = "light") -> Optional[str]:
        entities = self.list_entities(domain)
        if not entities:
            return None
        room = (room or "").lower()
        device = (device or "").lower()
        best = None
        best_score = 0
        for e in entities:
            eid = e.get("entity_id", "").lower()
            name = (e.get("attributes", {}) or {}).get("friendly_name", "").lower()
            haystack = f"{eid} {name}"
            score = 0
            if room and room in haystack:
                score += 2
            if device and device in haystack:
                score += 2
            if device and device in eid:
                score += 1
            if score > best_score:
                best_score = score
                best = e.get("entity_id")
        if best:
            logger.debug(f"[HomeAssistant] Resolved {room}/{device} ({domain}) -> {best}")
        return best

    @staticmethod
    def _format_entities_list(entities: List[Dict[str, Any]]) -> str:
        if not entities:
            return "No entities found. Make sure Home Assistant is reachable and you specified the right device type."
        lines = []
        for e in entities[:20]:
            eid = e.get("entity_id", "?")
            fname = (e.get("attributes", {}) or {}).get("friendly_name", eid)
            state = e.get("state", "?")
            lines.append(f"- {fname} [{eid}] => {state}")
        header = f"Found {len(entities)} device(s):"
        if len(entities) > 20:
            header += f" (showing first 20)"
        return header + "\n" + "\n".join(lines)

    @staticmethod
    def skill_handle(text: str, assistant_ref: Any = None) -> Optional[Dict[str, Any]]:
        if not isinstance(text, str):
            return None
        low = text.lower()

        ha = HomeAssistantBridge()

        list_match = re.search(r"\b(list all devices|list devices|show all devices|what devices do i have|get device list)\b", low)
        if list_match:
            if not ha._configured():
                return {"text": "Home Assistant is not configured. Set HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN in your environment to enable smart home control.", "intent": "smarthome_list", "warning": True}
            entities = ha.list_entities("")
            return {
                "text": HomeAssistantBridge._format_entities_list(entities),
                "intent": "smarthome_list",
                "data": {"entities": entities},
            }

        temp_q = re.search(r"\b(what(?:'s| is) the (temperature|climate|temp)|current temperature|how (hot|cold|warm) is it|room temp|climate status)\b", low)
        if temp_q:
            if not ha._configured():
                return {"text": "Home Assistant is not configured.", "intent": "smarthome_climate", "warning": True}
            climates = ha.list_entities("climate")
            sensors = ha.list_entities("sensor")
            temp_entity = None
            temp_value = None
            unit = None
            for c in climates[:3]:
                attrs = c.get("attributes", {}) or {}
                if attrs.get("current_temperature") is not None:
                    temp_value = attrs["current_temperature"]
                    unit = attrs.get("temperature_unit", "°C")
                    temp_entity = c.get("entity_id")
                    break
            if temp_value is None:
                for s in sensors:
                    aid = s.get("attributes", {}) or {}
                    device_class = aid.get("device_class", "")
                    unit_measure = aid.get("unit_of_measurement", "")
                    if device_class == "temperature" or unit_measure in ("°C", "°F", "C", "F"):
                        try:
                            temp_value = float(s.get("state"))
                            unit = unit_measure or "°C"
                            temp_entity = s.get("entity_id")
                            break
                        except Exception:
                            continue
            if temp_value is not None:
                return {
                    "text": f"The current temperature is {temp_value}{unit}. (Sensor: {temp_entity})",
                    "intent": "smarthome_climate",
                    "data": {"temperature": temp_value, "unit": unit, "entity_id": temp_entity},
                }
            return {"text": "I couldn't find a temperature or climate entity in Home Assistant. Make sure a climate or temperature sensor is available.", "intent": "smarthome_climate", "warning": True}

        cam_match = re.search(r"\b(show|display|open|view|grab|snap|look at)\s+(?:the\s+)?(?:camera\s+)?([A-Za-z0-9_\- ]+?)\s*(?:camera)?(?:\s*please)?[.!?]*$", low)
        if cam_match:
            camera_name = cam_match.group(2).strip()
            if not ha._configured():
                return {"text": "Home Assistant is not configured; can't fetch camera snapshots.", "intent": "smarthome_camera", "warning": True}
            entity_id = ha._find_entity(camera_name, camera_name, "camera")
            if not entity_id and re.match(r"^camera\.[a-z0-9_]+$", camera_name.lower()):
                entity_id = camera_name.lower()
            if not entity_id:
                return {"text": f"I couldn't find a camera matching '{camera_name}'. Try the exact entity_id like camera.front_door.", "intent": "smarthome_camera", "warning": True}
            from datetime import datetime
            safe = re.sub(r"[^A-Za-z0-9_\-]", "_", entity_id)
            save_path = str(CAMERAS_DIR / f"{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
            result = ha.get_camera_snapshot(entity_id, save_path)
            if result:
                return {
                    "text": f"Got it. Snapshot from {entity_id} saved at {result}",
                    "intent": "smarthome_camera",
                    "data": {"image_path": result, "entity_id": entity_id},
                }
            return {"text": f"Couldn't fetch a snapshot from {entity_id}. Check that the camera is online in Home Assistant.", "intent": "smarthome_camera", "error": True}

        thermo_match = re.search(
            r"\bset\s+(?:the\s+)?(?:thermostat|ac|air conditioner|heater|climate|temperature)\s+(?:in\s+(?:the\s+)?([A-Za-z0-9_ ]+?)\s+)?to\s+(\d+(?:\.\d+)?)\s*°?\s*(c|f|celcius|celsius|fahrenheit)?",
            low, re.IGNORECASE)
        if thermo_match:
            room = (thermo_match.group(1) or "").strip()
            temp_str = thermo_match.group(2)
            unit_raw = (thermo_match.group(3) or "").lower()
            unit = "°C" if unit_raw in ("c", "celcius", "celsius", "") else "°F"
            try:
                temp_value = float(temp_str)
            except Exception:
                return {"text": f"Could not parse temperature from: '{text}'", "intent": "smarthome_climate_set", "error": True}
            if not ha._configured():
                return {"text": "Home Assistant is not configured.", "intent": "smarthome_climate_set", "warning": True}
            entity_id = ha._find_entity(room, "thermostat", "climate") or ha._find_entity(room, "ac", "climate")
            if not entity_id:
                climates = ha.list_entities("climate")
                if climates:
                    entity_id = climates[0].get("entity_id")
            if not entity_id:
                return {"text": "I couldn't find any climate/thermostat entity. Try the full entity_id like climate.living_room.", "intent": "smarthome_climate_set", "warning": True}
            svc_data = {
                "entity_id": entity_id,
                "temperature": temp_value,
            }
            if unit == "°F":
                svc_data["temperature_unit"] = "fahrenheit"
            else:
                svc_data["temperature_unit"] = "celsius"
            res = ha.call_service("climate", "set_temperature", svc_data)
            if res.get("success"):
                return {
                    "text": f"Thermostat set to {temp_value}{unit} on {entity_id}.",
                    "intent": "smarthome_climate_set",
                    "data": res,
                }
            return {
                "text": f"Failed to set thermostat. Home Assistant says: {res.get('error') or res.get('response', 'unknown error')}",
                "intent": "smarthome_climate_set",
                "error": True,
                "data": res,
            }

        turn_match = re.search(
            r"\b(turn|switch|power)\s+(on|off)\s+(?:the\s+)?(?:([A-Za-z0-9_ ]+?)\s+)?(?:([A-Za-z0-9_\- ]+?))\s*[.!?]*$",
            low)
        if turn_match:
            on_off = turn_match.group(2).lower()
            room = (turn_match.group(3) or "").strip()
            device = (turn_match.group(4) or "").strip()
            if not device:
                return None
            if not ha._configured():
                return {"text": "Home Assistant is not configured; can't control devices yet.", "intent": f"smarthome_turn_{on_off}", "warning": True}
            domain = "light"
            dev_low = device.lower()
            if any(k in dev_low for k in ["switch", "plug", "outlet", "socket"]):
                domain = "switch"
            elif any(k in dev_low for k in ["fan"]):
                domain = "fan"
            entity_id = ha._find_entity(room, device, domain)
            if not entity_id:
                for d in ("light", "switch", "fan", "cover", "media_player"):
                    entity_id = ha._find_entity(room, device, d)
                    if entity_id:
                        domain = d
                        break
            if not entity_id and re.match(r"^[a-z]+\.[a-z0-9_]+$", device.lower()):
                entity_id = device.lower()
                domain = entity_id.split(".")[0]
            if not entity_id:
                return {
                    "text": f"I couldn't find a {domain} matching '{room} {device}'. Please use the exact entity_id or make sure the device is exposed in Home Assistant.",
                    "intent": f"smarthome_turn_{on_off}",
                    "warning": True,
                }
            if on_off == "on":
                res = ha.turn_on(entity_id)
            else:
                res = ha.turn_off(entity_id)
            if res.get("success"):
                return {
                    "text": f"Okay, turned {on_off} {entity_id}.",
                    "intent": f"smarthome_turn_{on_off}",
                    "data": res,
                }
            return {
                "text": f"Failed to turn {on_off} {entity_id}: {res.get('error') or res.get('response', 'unknown error')}",
                "intent": f"smarthome_turn_{on_off}",
                "error": True,
                "data": res,
            }

        return None

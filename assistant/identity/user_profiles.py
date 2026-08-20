import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from ..utils.logger import logger
from ..config import settings


class UserProfileManager:
    def __init__(self, profiles_path: Optional[str] = None, encodings_path: Optional[str] = None):
        self.profiles_path = Path(profiles_path or settings.user_profiles_path)
        self.encodings_path = Path(encodings_path or settings.face_encodings_path)
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.face_encodings: Dict[str, Any] = {}
        self.tolerance = settings.face_recognition_tolerance
        self._load_profiles()
        self._load_encodings()

    def _load_profiles(self):
        if self.profiles_path.exists():
            try:
                with open(self.profiles_path, "r", encoding="utf-8") as f:
                    self.profiles = json.load(f)
                logger.info(f"[UserProfiles] Loaded {len(self.profiles)} user profiles")
            except Exception as e:
                logger.warning(f"[UserProfiles] Load failed: {e}")
                self.profiles = {}
        if "default" not in self.profiles:
            self.profiles["default"] = {
                "id": "default",
                "name": "Guest",
                "role": "guest",
                "language": "en-US",
                "tts_voice_gender": "neutral",
                "tts_rate": 200,
                "wake_word": settings.wake_word,
                "can_shutdown_pc": False,
                "can_delete_files": False,
                "calendar_id": None,
                "email": None,
                "custom_skills": [],
                "created_at": None,
            }
            self._save_profiles()

    def _save_profiles(self):
        try:
            self.profiles_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.profiles_path, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"[UserProfiles] Save failed: {e}")

    def _load_encodings(self):
        if self.encodings_path.exists():
            try:
                with open(self.encodings_path, "rb") as f:
                    self.face_encodings = pickle.load(f)
                logger.info(f"[UserProfiles] Loaded {len(self.face_encodings)} face encodings")
            except Exception as e:
                logger.debug(f"[UserProfiles] Encodings load failed: {e}")
                self.face_encodings = {}

    def _save_encodings(self):
        try:
            self.encodings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.encodings_path, "wb") as f:
                pickle.dump(self.face_encodings, f)
        except Exception as e:
            logger.warning(f"[UserProfiles] Encodings save failed: {e}")

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.profiles.get(user_id)

    def create_profile(
        self,
        user_id: str,
        name: str,
        role: str = "user",
        language: str = "en-US",
        tts_voice_gender: str = "neutral",
        can_shutdown_pc: bool = False,
        can_delete_files: bool = False,
        email: Optional[str] = None,
        extra: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        import datetime as _dt
        profile = {
            "id": user_id,
            "name": name,
            "role": role,
            "language": language,
            "tts_voice_gender": tts_voice_gender,
            "tts_rate": 200,
            "wake_word": settings.wake_word,
            "can_shutdown_pc": can_shutdown_pc,
            "can_delete_files": can_delete_files,
            "calendar_id": None,
            "email": email,
            "custom_skills": [],
            "created_at": _dt.datetime.now().isoformat(),
        }
        if extra:
            profile.update(extra)
        self.profiles[user_id] = profile
        self._save_profiles()
        logger.info(f"[UserProfiles] Created profile: {name} ({user_id}, role={role})")
        return profile

    def update_profile(self, user_id: str, **kwargs) -> bool:
        if user_id not in self.profiles:
            return False
        self.profiles[user_id].update(kwargs)
        self._save_profiles()
        return True

    def delete_profile(self, user_id: str) -> bool:
        if user_id == "default":
            return False
        if user_id in self.profiles:
            del self.profiles[user_id]
            self.face_encodings.pop(user_id, None)
            self._save_profiles()
            self._save_encodings()
            return True
        return False

    def list_profiles(self) -> List[Dict[str, Any]]:
        return [{"id": k, "name": v.get("name", "?"), "role": v.get("role")} for k, v in self.profiles.items()]

    def has_permission(self, user_id: str, permission: str) -> bool:
        p = self.profiles.get(user_id) or self.profiles.get("default")
        if not p:
            return False
        if p.get("role") == "admin":
            return True
        return bool(p.get(permission, False))

    def register_face_from_image(self, user_id: str, image_path: str) -> bool:
        try:
            import face_recognition
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if not encodings:
                logger.warning(f"[UserProfiles] No face found in {image_path}")
                return False
            import datetime as _dt
            self.face_encodings[user_id] = {
                "encoding": encodings[0].tolist(),
                "name": self.profiles.get(user_id, {}).get("name", user_id),
                "added_at": _dt.datetime.now().isoformat(),
            }
            self._save_encodings()
            logger.info(f"[UserProfiles] Registered face for {user_id}")
            return True
        except ImportError:
            logger.warning("[UserProfiles] face_recognition package not installed")
            return False
        except Exception as e:
            logger.warning(f"[UserProfiles] Register face failed: {e}")
            return False

    def identify_from_frame(self, frame) -> Optional[Tuple[str, str]]:
        try:
            import face_recognition
            import numpy as np
            if not self.face_encodings:
                return None
            rgb = frame[:, :, ::-1]
            encs = face_recognition.face_encodings(rgb)
            if not encs:
                return None
            known_ids = list(self.face_encodings.keys())
            known = [np.array(self.face_encodings[k]["encoding"]) for k in known_ids]
            for enc in encs:
                results = face_recognition.compare_faces(known, enc, tolerance=self.tolerance)
                dists = face_recognition.face_distance(known, enc)
                if True in results:
                    best_idx = int(np.argmin(dists))
                    if results[best_idx]:
                        uid = known_ids[best_idx]
                        return uid, self.face_encodings[uid].get("name", uid)
            return None
        except ImportError:
            return None
        except Exception as e:
            logger.debug(f"[UserProfiles] Identify error: {e}")
            return None

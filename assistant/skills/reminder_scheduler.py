import json
import re
import datetime
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    _APSCHEDULER_AVAILABLE = True
except ImportError:
    BackgroundScheduler = None  # type: ignore
    DateTrigger = None  # type: ignore
    IntervalTrigger = None  # type: ignore
    CronTrigger = None  # type: ignore
    _APSCHEDULER_AVAILABLE = False

from ..utils.logger import logger
from ..config import settings


class ReminderScheduler:
    def __init__(self, db_path: Optional[str] = None, on_fire: Optional[Callable] = None):
        self.db_path = Path(db_path or settings.reminder_db_path)
        self.on_fire = on_fire
        self.reminders: List[Dict[str, Any]] = []
        self.scheduler: Optional[BackgroundScheduler] = None
        self._running = False
        self._load()

    def _load(self):
        if self.db_path.exists():
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.reminders = json.load(f)
                logger.info(f"[ReminderScheduler] Loaded {len(self.reminders)} reminders from disk")
            except Exception as e:
                logger.warning(f"[ReminderScheduler] Load failed: {e}")
                self.reminders = []
        else:
            self.reminders = []

    def _save(self):
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.reminders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"[ReminderScheduler] Save failed: {e}")

    def start(self):
        if self._running:
            return
        if not _APSCHEDULER_AVAILABLE:
            logger.warning("[ReminderScheduler] APScheduler not installed; reminders stored but no background jobs will fire. pip install apscheduler")
            self._running = False
            return
        try:
            self.scheduler = BackgroundScheduler(timezone=datetime.datetime.now().astimezone().tzinfo)
            self.scheduler.start()
            self._running = True
            now = datetime.datetime.now()
            restored = 0
            expired = 0
            for r in list(self.reminders):
                if r.get("fired") or r.get("cancelled"):
                    continue
                dt = self._parse_isotime(r.get("fire_at"))
                if dt and dt < now and r.get("recurrence") in (None, "once"):
                    r["fired"] = True
                    expired += 1
                    continue
                if dt:
                    self._schedule_job(r)
                    restored += 1
            if expired:
                self._save()
            logger.info(f"[ReminderScheduler] Started. Restored {restored} scheduled jobs, {expired} expired removed.")
        except Exception as e:
            logger.error(f"[ReminderScheduler] Failed to start scheduler: {e}")
            self._running = False

    def stop(self):
        if self.scheduler and self._running:
            try:
                self.scheduler.shutdown(wait=False)
            except Exception:
                pass
            self._running = False
            logger.info("[ReminderScheduler] Stopped.")

    def _parse_isotime(self, s: Optional[str]) -> Optional[datetime.datetime]:
        if not s:
            return None
        try:
            return datetime.datetime.fromisoformat(s)
        except Exception:
            return None

    def _fire_reminder(self, reminder_id: str):
        match = next((r for r in self.reminders if r["id"] == reminder_id), None)
        if not match or match.get("cancelled") or match.get("fired"):
            return
        match["fired"] = True
        match["fired_at"] = datetime.datetime.now().isoformat()
        if match.get("recurrence") in (None, "once"):
            pass
        else:
            match["fired"] = False
        self._save()
        text = match.get("text", "")
        logger.info(f"[ReminderScheduler] 🔔 Reminder fired: {text}")
        if self.on_fire:
            try:
                self.on_fire(match)
            except Exception as e:
                logger.error(f"[ReminderScheduler] on_fire callback error: {e}")

    def _schedule_job(self, reminder: Dict[str, Any]):
        if not self.scheduler:
            return
        rid = reminder["id"]
        rec = reminder.get("recurrence")
        try:
            if rec in (None, "once"):
                dt = self._parse_isotime(reminder.get("fire_at"))
                if dt:
                    self.scheduler.add_job(
                        self._fire_reminder,
                        trigger=DateTrigger(run_date=dt),
                        args=[rid],
                        id=f"rem_{rid}",
                        replace_existing=True,
                    )
            elif rec == "interval":
                secs = reminder.get("interval_seconds", 3600)
                self.scheduler.add_job(
                    self._fire_reminder,
                    trigger=IntervalTrigger(seconds=secs),
                    args=[rid],
                    id=f"rem_{rid}",
                    replace_existing=True,
                )
            elif rec == "cron":
                cron = reminder.get("cron", {})
                self.scheduler.add_job(
                    self._fire_reminder,
                    trigger=CronTrigger(**{k: v for k, v in cron.items() if v is not None}),
                    args=[rid],
                    id=f"rem_{rid}",
                    replace_existing=True,
                )
        except Exception as e:
            logger.warning(f"[ReminderScheduler] Schedule failed for {rid}: {e}")

    def add_reminder(
        self,
        text: str,
        when: Optional[datetime.datetime] = None,
        recurrence: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        cron: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        rid = f"rem_{abs(hash(text + datetime.datetime.now().isoformat())) % 1000000}"
        reminder: Dict[str, Any] = {
            "id": rid,
            "text": text,
            "created_at": datetime.datetime.now().isoformat(),
            "fire_at": when.isoformat() if when else None,
            "recurrence": recurrence,
            "interval_seconds": interval_seconds,
            "cron": cron,
            "fired": False,
            "cancelled": False,
            "extra": extra or {},
        }
        self.reminders.append(reminder)
        self._save()
        if self._running:
            self._schedule_job(reminder)
        logger.info(f"[ReminderScheduler] Added reminder: {text} (id={rid})")
        return reminder

    def parse_and_add(self, text: str, natural: str) -> Dict[str, Any]:
        when = self._parse_natural_time(natural)
        if when is None and "every" in natural.lower():
            return self.add_reminder(
                text,
                recurrence="interval",
                interval_seconds=self._parse_interval(natural),
            )
        if "weekday" in natural.lower() or "at " in natural.lower() and "every" in natural.lower():
            cron = self._parse_cron(natural)
            return self.add_reminder(text, recurrence="cron", cron=cron)
        return self.add_reminder(text, when=when)

    def _parse_natural_time(self, s: str) -> Optional[datetime.datetime]:
        now = datetime.datetime.now()
        sl = s.lower()
        try:
            m = re.search(r"in\s+(\d+)\s*(minute|min|minutes|m)\b", sl)
            if m:
                return now + datetime.timedelta(minutes=int(m.group(1)))
            m = re.search(r"in\s+(\d+)\s*(hour|hr|hours|h)\b", sl)
            if m:
                return now + datetime.timedelta(hours=int(m.group(1)))
            m = re.search(r"in\s+(\d+)\s*(day|days|d)\b", sl)
            if m:
                return now + datetime.timedelta(days=int(m.group(1)))
            m = re.search(r"at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", sl)
            if m:
                h = int(m.group(1))
                mi = int(m.group(2) or 0)
                ampm = m.group(3)
                if ampm == "pm" and h < 12:
                    h += 12
                if ampm == "am" and h == 12:
                    h = 0
                dt = now.replace(hour=h, minute=mi, second=0, microsecond=0)
                if dt <= now:
                    dt += datetime.timedelta(days=1)
                return dt
            if "tomorrow" in sl:
                dt = now + datetime.timedelta(days=1)
                return dt.replace(hour=9, minute=0, second=0, microsecond=0)
            if "tonight" in sl:
                return now.replace(hour=20, minute=0, second=0, microsecond=0)
        except Exception:
            pass
        return None

    def _parse_interval(self, s: str) -> int:
        sl = s.lower()
        m = re.search(r"every\s+(\d+)\s*(minute|hour|day)", sl)
        if m:
            n = int(m.group(1))
            u = m.group(2)
            if u.startswith("minute"):
                return n * 60
            if u.startswith("hour"):
                return n * 3600
            if u.startswith("day"):
                return n * 86400
        return 3600

    def _parse_cron(self, s: str) -> Dict[str, Any]:
        cron: Dict[str, Any] = {}
        sl = s.lower()
        m = re.search(r"at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", sl)
        if m:
            h = int(m.group(1))
            mi = int(m.group(2) or 0)
            ampm = m.group(3)
            if ampm == "pm" and h < 12:
                h += 12
            if ampm == "am" and h == 12:
                h = 0
            cron["hour"] = h
            cron["minute"] = mi
        if "weekday" in sl:
            cron["day_of_week"] = "mon-fri"
        if "monday" in sl:
            cron["day_of_week"] = "mon"
        return cron

    def list_reminders(self, include_fired: bool = False) -> List[Dict[str, Any]]:
        if include_fired:
            return list(self.reminders)
        return [r for r in self.reminders if not r.get("fired") and not r.get("cancelled")]

    def cancel(self, reminder_id: str) -> bool:
        match = next((r for r in self.reminders if r["id"] == reminder_id), None)
        if not match:
            return False
        match["cancelled"] = True
        if self.scheduler:
            try:
                self.scheduler.remove_job(f"rem_{reminder_id}")
            except Exception:
                pass
        self._save()
        return True

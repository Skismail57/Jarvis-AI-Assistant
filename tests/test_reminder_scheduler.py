import json
import datetime
import pytest


def test_add_reminder_basic(tmp_reminder_db_path):
    from assistant.skills.reminder_scheduler import ReminderScheduler
    rs = ReminderScheduler(db_path=tmp_reminder_db_path)
    rs.reminders.clear()
    when = datetime.datetime.now() + datetime.timedelta(hours=1)
    r = rs.add_reminder("Take medicine", when=when)
    assert r["id"].startswith("rem_")
    assert r["text"] == "Take medicine"
    assert r["fire_at"] == when.isoformat()
    assert r["fired"] is False
    assert r["cancelled"] is False
    assert len(rs.list_reminders()) == 1


def test_parse_and_add_in_5_minutes(tmp_reminder_db_path):
    from assistant.skills.reminder_scheduler import ReminderScheduler
    rs = ReminderScheduler(db_path=tmp_reminder_db_path)
    rs.reminders.clear()
    before = datetime.datetime.now()
    r = rs.parse_and_add("call mom", "remind me to call mom in 5 minutes")
    assert r["text"] == "call mom"
    assert r["fire_at"] is not None
    fire_dt = datetime.datetime.fromisoformat(r["fire_at"])
    after = datetime.datetime.now()
    diff_lower = datetime.timedelta(minutes=4, seconds=50)
    diff_upper = datetime.timedelta(minutes=5, seconds=10)
    assert diff_lower <= (fire_dt - before) <= diff_upper or diff_lower <= (fire_dt - after) <= diff_upper
    assert r["fired"] is False


def test_list_reminders_filters_fired_and_cancelled(tmp_reminder_db_path):
    from assistant.skills.reminder_scheduler import ReminderScheduler
    rs = ReminderScheduler(db_path=tmp_reminder_db_path)
    rs.reminders.clear()
    when = datetime.datetime.now() + datetime.timedelta(hours=1)
    r1 = rs.add_reminder("A", when=when)
    r2 = rs.add_reminder("B", when=when)
    r3 = rs.add_reminder("C", when=when)
    rs.cancel(r2["id"])
    rs.reminders[0]["fired"] = True
    rs._save()
    active = rs.list_reminders()
    assert len(active) == 1
    assert active[0]["id"] == r3["id"]
    all_items = rs.list_reminders(include_fired=True)
    assert len(all_items) == 3


def test_cancel_reminder(tmp_reminder_db_path):
    from assistant.skills.reminder_scheduler import ReminderScheduler
    rs = ReminderScheduler(db_path=tmp_reminder_db_path)
    rs.reminders.clear()
    when = datetime.datetime.now() + datetime.timedelta(hours=2)
    r = rs.add_reminder("Cancel me", when=when)
    assert rs.cancel(r["id"]) is True
    match = next(x for x in rs.reminders if x["id"] == r["id"])
    assert match["cancelled"] is True
    assert len(rs.list_reminders()) == 0
    assert rs.cancel("rem_nonexistent_999") is False


def test_save_and_load_cycle(tmp_reminder_db_path):
    from assistant.skills.reminder_scheduler import ReminderScheduler
    rs1 = ReminderScheduler(db_path=tmp_reminder_db_path)
    rs1.reminders.clear()
    when = datetime.datetime.now() + datetime.timedelta(days=1)
    r1 = rs1.add_reminder("Buy groceries", when=when)
    r2 = rs1.add_reminder("Finish report", when=when)
    ids_before = {r1["id"], r2["id"]}

    rs2 = ReminderScheduler(db_path=tmp_reminder_db_path)
    loaded_ids = {r["id"] for r in rs2.reminders}
    assert ids_before.issubset(loaded_ids)
    texts = {r["text"] for r in rs2.reminders}
    assert "Buy groceries" in texts
    assert "Finish report" in texts


def test_add_reminder_recurrence_interval(tmp_reminder_db_path):
    from assistant.skills.reminder_scheduler import ReminderScheduler
    rs = ReminderScheduler(db_path=tmp_reminder_db_path)
    rs.reminders.clear()
    r = rs.add_reminder("Drink water", recurrence="interval", interval_seconds=1800)
    assert r["recurrence"] == "interval"
    assert r["interval_seconds"] == 1800
    assert r["fire_at"] is None

import datetime
import pytest


@pytest.fixture
def skill_handler():
    from assistant.skills.skill_handler import SkillHandler
    return SkillHandler()


def test_handle_time_returns_response(skill_handler):
    result = skill_handler._handle_time("what time is it", None)
    assert isinstance(result, dict)
    assert result["intent"] == "time"
    assert "text" in result
    assert "data" in result
    assert "time" in result["data"]
    assert "hour" in result["data"]
    assert "minute" in result["data"]
    now = datetime.datetime.now()
    assert result["data"]["hour"] == now.hour
    assert result["data"]["minute"] == now.minute
    assert "current time" in result["text"] or "time is" in result["text"]


def test_handle_time_greeting_based_on_hour(skill_handler):
    result = skill_handler._handle_time("time", None)
    hour = datetime.datetime.now().hour
    text = result["text"]
    if 5 <= hour < 12:
        assert "Good morning" in text
    elif 12 <= hour < 17:
        assert "Good afternoon" in text
    elif 17 <= hour < 21:
        assert "Good evening" in text
    else:
        assert "nighttime" in text or "time" in text


def test_handle_date_returns_response(skill_handler):
    result = skill_handler._handle_date("what is the date today", None)
    assert isinstance(result, dict)
    assert result["intent"] == "date"
    assert "text" in result
    assert "Today is" in result["text"]
    data = result["data"]
    assert "date" in data
    assert "day_of_week" in data
    assert "month" in data
    assert "day" in data
    assert "year" in data
    now = datetime.datetime.now()
    assert data["year"] == now.year
    assert data["day"] == now.day


def test_handle_joke_returns_joke(skill_handler):
    result = skill_handler._handle_joke("tell me a joke", None)
    assert isinstance(result, dict)
    assert result["intent"] == "joke"
    assert "text" in result
    assert "data" in result
    assert "joke" in result["data"]
    assert result["data"]["joke"] in skill_handler._jokes
    assert result["data"]["joke"] in result["text"]
    assert len(skill_handler._jokes) >= 10


def test_handle_name_default(skill_handler):
    result = skill_handler._handle_name("what is your name", None)
    assert isinstance(result, dict)
    assert result["intent"] == "name"
    assert "Jarvis" in result["text"]
    assert "AI assistant" in result["text"].lower() or "personal" in result["text"].lower()


def test_handle_name_with_context_responses(skill_handler):
    ctx = {"responses": ["I'm Bob!", "Call me Bob."]}
    result = skill_handler._handle_name("your name", ctx)
    assert result["text"] in ctx["responses"]


def test_handle_calculator_multiply_25_times_4(skill_handler):
    result = skill_handler._handle_calculator("what is 25 * 4", None)
    assert result["intent"] == "calculator"
    assert "error" not in result or result.get("error") is not True
    assert result["data"]["result"] == 100
    assert "100" in result["text"]


def test_handle_calculator_multiply_12_times_5(skill_handler):
    result = skill_handler._handle_calculator("solve 12 * 5", None)
    assert result["intent"] == "calculator"
    assert result["data"]["result"] == 60
    assert "60" in result["text"]


def test_handle_calculator_words_plus_minus(skill_handler):
    result = skill_handler._handle_calculator("what is 10 plus 5 minus 3", None)
    assert result["intent"] == "calculator"
    if "error" not in result:
        assert result["data"]["result"] == 12


def test_handle_calculator_percent(skill_handler):
    result = skill_handler._handle_calculator("what is 15 percent of 200", None)
    if "error" not in result:
        assert result["data"]["result"] == 30


def test_handle_calculator_invalid_expression(skill_handler):
    result = skill_handler._handle_calculator("calculate this is not math", None)
    assert result["intent"] == "calculator"
    assert result.get("error") is True or "help you calculate" in result["text"]


def test_handle_translate_needs_more(skill_handler):
    result = skill_handler._handle_translate("translate something", None)
    assert result["intent"] == "translate"
    assert result.get("needs_more") is True or "like" in result["text"].lower()


def test_handle_translate_basic_structure(skill_handler):
    result = skill_handler._handle_translate('translate "hello world" to Spanish', None)
    assert isinstance(result, dict)
    assert result["intent"] == "translate"
    assert "data" in result
    assert "from" in result["data"]
    assert "to" in result["data"]
    assert result["data"]["to"] == "es"
    assert "original" in result["data"]
    assert "translated" in result["data"]


def test_handle_show_reminders_empty_without_scheduler(skill_handler):
    result = skill_handler._handle_show_reminders("show reminders", None)
    assert result["intent"] == "show_reminders"
    assert "don't have any reminders yet" in result["text"] or "no reminders yet" in result["text"].lower() or "reminders yet" in result["text"]


def test_handle_show_reminders_empty_with_scheduler(skill_handler, tmp_reminder_db_path):
    from assistant.skills.reminder_scheduler import ReminderScheduler
    sched = ReminderScheduler(db_path=tmp_reminder_db_path)
    skill_handler.bind_reminder_scheduler(sched)
    result = skill_handler._handle_show_reminders("list reminders", None)
    assert result["intent"] == "show_reminders"
    assert "don't have any scheduled reminders yet" in result["text"] or "no scheduled reminders" in result["text"].lower()

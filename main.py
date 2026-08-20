#!/usr/bin/env python3
"""
JARVIS - Professional AI Personal Assistant
Built with Python, Machine Learning, and Deep Learning

Usage:
    python main.py                      # Text mode (default, no mic needed
    python main.py --voice              # Voice input + voice output
    python main.py --wake             # Continuous wake-word mode
    python main.py --text             # Text-only mode
    python main.py --test             # Run quick diagnostic tests
    python main.py --retrain          # Retrain the intent classifier
    python main.py --llm gpt-4o       # Use specific LLM model
"""

import sys
import os
import argparse

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

LOCAL_PKGS = os.path.join(ROOT_DIR, "_pkgs")
if os.path.isdir(LOCAL_PKGS):
    if LOCAL_PKGS not in sys.path:
        sys.path.insert(0, LOCAL_PKGS)
    bin_dir = os.path.join(LOCAL_PKGS, "bin")
    if os.path.isdir(bin_dir):
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")

from assistant.core.assistant import AIAssistant
from assistant.nlp.intent_classifier import IntentClassifier


ASSISTANT_NAME = "Jarvis"
WAKE_WORD = "jarvis"


def run_tests():
    print("\n" + "=" * 70)
    print(f"  Running JARVIS - Personal AI Assistant - Diagnostic Tests")
    print("=" * 70 + "\n")

    tests_passed = 0
    tests_total = 0

    print("[1/7] Testing Intent Classifier (ML)...")
    tests_total += 1
    try:
        clf = IntentClassifier()
        test_phrases = [
            ("hello", "greeting"),
            ("what time is it", "time"),
            ("what is the date today", "date"),
            ("weather in new york", "weather"),
            ("what is 12 * 5", "calculator"),
            ("remind me to buy groceries", "reminder"),
            ("tell me a joke", "joke"),
            ("what is your name", "name"),
            ("bye bye", "farewell"),
            ("thank you very much", "thanks"),
        ]
        passed = 0
        for phrase, expected in test_phrases:
            result = clf.get_intent(phrase)
            actual = result["intent"]
            status = "[OK]" if actual == expected else "[FAIL]"
            if actual == expected:
                passed += 1
            print(f"  {status} '{phrase}' -> {actual} (expected: {expected}, conf: {result['confidence']:.2f})")
        ratio = passed / len(test_phrases)
        if ratio >= 0.7:
            tests_passed += 1
            print(f"  [PASS] Intent classifier: {passed}/{len(test_phrases)} patterns recognized.\n")
        else:
            print(f"  [WARN] Intent classifier below 70% accuracy: {passed}/{len(test_phrases)}.\n")
    except Exception as e:
        print(f"  [FAIL] Intent classifier failed: {e}\n")
        import traceback; traceback.print_exc()

    print("[2/7] Testing Skill Handler...")
    tests_total += 1
    try:
        from assistant.skills.skill_handler import SkillHandler
        sh = SkillHandler()
        r = sh.handle("time", "what time is it")
        assert "time" in r["intent"] and "current time" in r["text"].lower()
        r = sh.handle("date", "today's date")
        assert "date" in r["intent"] and "today is" in r["text"].lower()
        r = sh.handle("joke", "tell me a joke")
        assert r["intent"] == "joke" and len(r["text"]) > 20
        r = sh.handle("calculator", "what is 12 * 5")
        assert r["data"]["result"] == 60
        tests_passed += 1
        print("  [PASS] Skill handler working correctly.\n")
    except Exception as e:
        print(f"  [FAIL] Skill handler failed: {e}\n")
        import traceback; traceback.print_exc()

    print("[3/7] Testing Conversation Memory...")
    tests_total += 1
    try:
        from assistant.memory.conversation_memory import ConversationMemory
        mem = ConversationMemory()
        mem.clear()
        mem.add_user("hello there")
        mem.add_assistant("hi! how can I help?")
        assert mem.count() == 2
        recent = mem.get_recent_context(turns=1)
        assert "hello there" in recent and "how can I help" in recent
        tests_passed += 1
        print("  [PASS] Conversation memory working correctly.\n")
    except Exception as e:
        print(f"  [FAIL] Conversation memory failed: {e}\n")

    print("[4/7] Testing LLM Core (knowledge layer)...")
    tests_total += 1
    try:
        from assistant.core.llm_core import LLMCore
        llm = LLMCore()
        r = llm.answer("What is 2 + 2? Answer concisely.")
        assert r.text and len(r.text) > 0
        has_key = llm.has_any_key()
        if not has_key:
            print(f"  [WARN] LLM initialized (no API keys set — offline mode.)")
        else:
            print(f"  [PASS] LLM ready (provider chain available).")
        print(f"  (Example answer: {r.text[:120]})")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] LLM Core error: {e}")
        import traceback; traceback.print_exc()

    print("\n[5/7] Testing Data Provider (weather/country/currency/time)...")
    tests_total += 1
    try:
        from assistant.core.data_provider import DataProvider
        dp = DataProvider()
        country = dp.get_country("India")
        assert country and country["cca2"] == "IN"
        print(f"  [PASS] Country lookup: India (capital: {country['capital']}, population ~{country['population']//1_000_000}M, currency: {country['currency']['code']})")
        t = dp.get_time_in("UTC")
        assert "time" in t
        try:
            cc = dp.currency_convert(1.0, "USD", "INR")
            print(f"  [PASS] Currency: 1 USD ≈ {cc.get('converted','?')} INR ({cc.get('last_updated','?')})")
        except Exception as ce:
            print(f"  [WARN] Currency API fallback: {ce}")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] Data provider failed: {e}\n")
        import traceback; traceback.print_exc()

    print("\n[6/7] Testing PC Controller...")
    tests_total += 1
    try:
        from assistant.core.pc_controller import PCController
        pc = PCController()
        info = pc.system_info()
        assert "os" in info and "ram_total_gb" in info
        print(f"  [PASS] System info: {info['os']} | CPU cores: {info['cores_logical']} | RAM: {info['ram_total_gb']} GB")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] PC Controller failed: {e}\n")
        import traceback; traceback.print_exc()

    print("\n[7/7] Testing Core Assistant (full stack)...")
    tests_total += 1
    try:
        assistant = AIAssistant(name=ASSISTANT_NAME, use_voice=False, enable_agent=False)
        resp = assistant.chat_text("hello", speak=False)
        assert len(resp) > 0
        resp = assistant.chat_text("what time is it", speak=False)
        assert len(resp) > 0
        resp = assistant.chat_text("what is 25 * 4", speak=False)
        assert "100" in resp.lower() or "25 * 4" in resp.lower() or "100" in str(resp)
        tests_passed += 1
        print("  [PASS] Core assistant stack working correctly.\n")
    except Exception as e:
        print(f"  [FAIL] Core assistant failed: {e}\n")
        import traceback; traceback.print_exc()

    print("=" * 70)
    print(f"  Diagnostics complete! Passed: {tests_passed}/{tests_total}. "
          f"JARVIS is {'READY' if tests_passed == tests_total else 'NEEDS SETUP'}.")
    if tests_passed < tests_total:
        print("  Tip: install deps with: pip install -r requirements.txt")
        print("  Tip: set OPENAI_API_KEY or GEMINI_API_KEY in .env for full knowledge.")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description=f"{ASSISTANT_NAME} - Professional AI Personal Assistant with ML/DL & PC control"
    )
    parser.add_argument("--voice", action="store_true", help="Enable voice input and output mode (mic required)")
    parser.add_argument("--wake", action="store_true", help="Continuous wake-word mode (say 'jarvis' to wake)")
    parser.add_argument("--text", action="store_true", help="Text-only mode (no voice)")
    parser.add_argument("--test", action="store_true", help="Run diagnostic tests")
    parser.add_argument("--retrain", action="store_true", help="Retrain ML intent classifier from scratch")
    parser.add_argument("--stt-engine", default="sr", choices=["sr", "whisper"], help="Speech-to-text engine (default sr)")
    parser.add_argument("--tts-engine", default="pyttsx3", choices=["pyttsx3", "gtts"], help="Text-to-speech engine")
    parser.add_argument("--llm", default="auto", help="LLM model name (auto/gpt-4o/gemini-1.5-flash/claude-3-haiku)")
    parser.add_argument("--no-agent", action="store_true", help="Disable self-thinking agent (faster but dumber)")
    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    if args.retrain:
        print(f"[{ASSISTANT_NAME}] Re-training intent classifier...")
        model_path = os.path.join(os.path.dirname(__file__), "models", "intent_classifier.pkl")
        data_path = os.path.join(os.path.dirname(__file__), "models", "intents_data.pkl")
        for p in (model_path, data_path):
            if isinstance(p, str) and os.path.exists(p):
                os.remove(p)
        IntentClassifier()
        print(f"[{ASSISTANT_NAME}] Classifier retrained and saved.")
        return

    if args.wake:
        mode = "wake"
        use_voice = True
    elif args.voice:
        mode = "voice"
        use_voice = True
    else:
        mode = "text"
        use_voice = not args.text

    assistant = AIAssistant(
        name=ASSISTANT_NAME,
        wake_word=WAKE_WORD,
        use_voice=use_voice,
        stt_engine=args.stt_engine,
        tts_engine=args.tts_engine,
        llm_model=args.llm,
        enable_agent=not args.no_agent,
    )
    assistant.run_cli(mode=mode)


if __name__ == "__main__":
    main()

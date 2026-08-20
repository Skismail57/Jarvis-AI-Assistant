import sys
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
LOCAL_PKGS = os.path.join(ROOT_DIR, "_pkgs")
if os.path.isdir(LOCAL_PKGS) and LOCAL_PKGS not in sys.path:
    sys.path.insert(0, LOCAL_PKGS)

print("Python:", sys.version)
print("sys.path[0]:", sys.path[0])

pkgs = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("sklearn", "scikit-learn"),
    ("nltk", "nltk"),
    ("joblib", "joblib"),
    ("bs4", "beautifulsoup4"),
    ("requests", "requests"),
]
ok = True
for imp, name in pkgs:
    try:
        m = __import__(imp)
        v = getattr(m, "__version__", "?")
        print(f"  OK {name:25s} -> version {v}")
    except Exception as e:
        print(f"  MISSING {name:22s} -> {e}")
        ok = False

print("\nTrying assistant import:")
try:
    from assistant.core.assistant import AIAssistant
    print("  OK assistant.core.assistant import succeeded")
except Exception as e:
    import traceback
    print("  FAIL assistant import:")
    traceback.print_exc()
    ok = False

print("\nAll required packages OK:", ok)
sys.exit(0 if ok else 1)

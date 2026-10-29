import sys
import os

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from pathlib import Path

# Locate backend folder whether called from root or inner folder
current_dir = Path(__file__).resolve().parent

if (current_dir / "ai-crop-recommendation7" / "backend" / "app.py").exists():
    backend_path = current_dir / "ai-crop-recommendation7" / "backend"
elif (current_dir / "backend" / "app.py").exists():
    backend_path = current_dir / "backend"
else:
    found = list(current_dir.glob("**/backend/app.py"))
    if found:
        backend_path = found[0].parent
    else:
        print("[ERROR] Could not find backend/app.py. Please verify project structure.")
        sys.exit(1)

print(f"[INFO] Project backend found at: {backend_path}")
os.chdir(backend_path)
sys.path.insert(0, str(backend_path))

def start_server():
    import app
    print("=" * 60)
    print("🌾 AI Crop Advisor Server is starting!")
    print("👉 Open your browser at: http://127.0.0.1:5000")
    print("👉 Or: http://localhost:5000")
    print("=" * 60)
    # use_reloader=False prevents watchdog crashing on Windows path changes
    app.app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)

if __name__ == "__main__":
    start_server()

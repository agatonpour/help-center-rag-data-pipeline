import os
import sys
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Make src/ importable
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

def main():
    if load_dotenv:
        load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python main.py [updates|cleanup]")
        sys.exit(2)

    cmd = sys.argv[1].lower()

    if cmd == "updates":
        from support_sync.sync_updates import main as run_updates
        run_updates()
        return

    if cmd == "cleanup":
        from support_sync.sync_cleanup import main as run_cleanup
        run_cleanup()
        return

    print(f"Unknown command: {cmd}")
    print("Usage: python main.py [updates|cleanup]")
    sys.exit(2)

if __name__ == "__main__":
    main()

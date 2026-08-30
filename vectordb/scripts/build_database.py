import sys
from pathlib import Path

# Add project root to path so we can import src
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.pipeline import run_pipeline

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

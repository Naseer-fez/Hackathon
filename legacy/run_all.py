"""Convenience runner script for BIS-SpecAI backend server and test suite."""
from __future__ import annotations

import subprocess
import sys
from backend.config.settings import app_settings


def run_tests() -> int:
    """Execute pytest suite across all backend modules."""
    print("Running BIS-SpecAI test suite...")
    res = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
    return res.returncode


def start_backend() -> None:
    """Launch FastAPI backend server with Uvicorn."""
    import uvicorn
    print(f"Starting BIS-SpecAI Server on {app_settings.server.host}:{app_settings.server.port}...")
    uvicorn.run(
        "backend.main:app",
        host=app_settings.server.host,
        port=app_settings.server.port,
        reload=False,
    )


def main() -> None:
    """Main CLI entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        code = run_tests()
        sys.exit(code)
    start_backend()


if __name__ == "__main__":
    main()

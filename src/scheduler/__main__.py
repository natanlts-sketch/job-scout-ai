"""Start background scheduled searches (optional companion process)."""
from __future__ import annotations

import time

from src.core.config import load_config
from src.core.db import initialize_database
from src.core.logging_setup import setup_logging
from src.scheduler import start_scheduler, stop_scheduler


def main() -> None:
    setup_logging()
    initialize_database()
    config = load_config()
    hours = int((config.get("scheduler") or {}).get("default_frequency_hours", 24))
    start_scheduler(hours)
    print(f"Scheduler running every {hours} hours. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_scheduler()
        print("Stopped.")


if __name__ == "__main__":
    main()

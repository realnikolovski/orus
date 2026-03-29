import logging
from pathlib import Path

from config import Config


def setup_logging(config: Config) -> None:
    """Configure root logger once; avoids duplicate handlers on reruns."""
    if logging.getLogger().handlers:
        # Already configured (avoid duplicate handlers in Streamlit reruns)
        return

    level = getattr(logging, str(config.log_level).upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    file_path = Path(config.log_file)
    try:
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        handlers = [console_handler, file_handler]
    except Exception:
        # If file handler fails (e.g., permission issues), fall back to console only.
        handlers = [console_handler]

    logging.basicConfig(level=level, handlers=handlers)

    logging.getLogger(__name__).info(
        "Logging initialized", extra={"log_file": str(config.log_file), "level": level}
    )

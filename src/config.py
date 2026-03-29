from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Config:
    db_path: str = os.getenv("ORUS_DB_PATH", "orus.db")
    log_level: str = os.getenv("ORUS_LOG_LEVEL", "INFO")
    log_file: str = os.getenv("ORUS_LOG_FILE", "orus.log")


def load_config() -> Config:
    return Config()

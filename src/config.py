from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Config:
    db_path: str = os.getenv("ORUS_DB_PATH", "orus.db")
    log_level: str = os.getenv("ORUS_LOG_LEVEL", "INFO")

def load_config() -> Config:
    return Config()

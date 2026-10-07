import os
from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class Settings:
    log_dir: Path

    MODEL_URL: str
    EMBEDDING_MODEL: str
    LLM_MODEL: str
    CLASSIFICATION_MODEL: str

    GUARDRAIL_LLM_ENABLED: bool
    GUARDRAIL_FAIL_OPEN: bool
    GUARDRAIL_BLOCK_CONFIDENCE: float

    MAX_QUERY_CHARS: int
    MIN_QUERY_CHARS: int

    @property
    def trace_file(self) -> Path:
        return self.log_dir / "traces.jsonl"

    @property
    def app_log_file(self) -> Path:
        return self.log_dir / "app.jsonl"


def str_to_bool(value: str) -> bool:
    return value.lower() in ("true", "1", "yes", "on")


@lru_cache(maxsize=1)
def get_settings() -> Settings:

    log_dir = Path(os.getenv("LOG_DIR", "./logs"))

    if not log_dir.is_absolute():
        log_dir = BASE_DIR / log_dir

    log_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        log_dir=log_dir,

        MODEL_URL=os.getenv("MODEL_URL", ""),
        EMBEDDING_MODEL=os.getenv("EMBEDDING_MODEL", ""),
        LLM_MODEL=os.getenv("LLM_MODEL", ""),
        CLASSIFICATION_MODEL=os.getenv("CLASSIFICATION_MODEL", ""),

        GUARDRAIL_LLM_ENABLED=str_to_bool(
            os.getenv("GUARDRAIL_LLM_ENABLED", "true")
        ),

        GUARDRAIL_FAIL_OPEN=str_to_bool(
            os.getenv("GUARDRAIL_FAIL_OPEN", "true")
        ),

        GUARDRAIL_BLOCK_CONFIDENCE=float(
            os.getenv("GUARDRAIL_BLOCK_CONFIDENCE", "0.8")
        ),

        MAX_QUERY_CHARS=int(
            os.getenv("MAX_QUERY_CHARS", "5000")
        ),

        MIN_QUERY_CHARS=int(
            os.getenv("MIN_QUERY_CHARS", "3")
        ),
    )
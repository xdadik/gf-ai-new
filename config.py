# pyre-ignore-all-errors
import os  # type: ignore  # pyre-ignore
from dataclasses import dataclass  # type: ignore  # pyre-ignore
from typing import FrozenSet, Optional  # type: ignore  # pyre-ignore

from dotenv import load_dotenv  # type: ignore  # pyre-ignore


def _parse_int_set(value: Optional[str]) -> FrozenSet[int]:  # type: ignore  # pyre-ignore
    if not value:
        return frozenset()
    items: list[int] = []  # type: ignore  # pyre-ignore
    for part in value.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            items.append(int(part))
        except ValueError:
            continue
    return frozenset(items)


def _parse_bool(value: Optional[str], default: bool = False) -> bool:  # type: ignore  # pyre-ignore
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


load_dotenv()


SYSTEM_PROMPT = ""


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str
    authorized_user_ids: FrozenSet[int]  # type: ignore  # pyre-ignore
    ollama_model: str
    ollama_base_url: str
    sqlite_path: str
    nova_log_file: str
    allowed_dir: str
    context_messages: int
    stream_edit_interval_s: float
    openweather_api_key: str
    custom_personalities_file: str
    allow_unsafe_file_ops: bool


def load_settings() -> Settings:  # type: ignore  # pyre-ignore
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    authorized = _parse_int_set(os.getenv("AUTHORIZED_USER_IDS"))
    # Back-compat: older single-id variable
    if not authorized:
        authorized = _parse_int_set(os.getenv("AUTHORIZED_USER_ID"))

    return Settings(
        telegram_bot_token=token,
        authorized_user_ids=authorized,
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b").strip(),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        sqlite_path=os.getenv("SQLITE_PATH", "nova.sqlite3").strip(),
        nova_log_file=os.getenv("NOVA_LOG_FILE", "nova.log").strip(),
        allowed_dir=os.getenv("ALLOWED_DIR", "./files_safe").strip(),
        context_messages=int(os.getenv("CONTEXT_MESSAGES", "8")),
        stream_edit_interval_s=float(os.getenv("STREAM_EDIT_INTERVAL_S", "0.4")),
        openweather_api_key=os.getenv("OPENWEATHER_API_KEY", "").strip(),
        custom_personalities_file=os.getenv("CUSTOM_PERSONALITIES_FILE", "custom_personalities.json").strip(),
        allow_unsafe_file_ops=_parse_bool(os.getenv("ALLOW_UNSAFE_FILE_OPS"), default=False),
    )


SETTINGS = load_settings()


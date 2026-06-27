from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ASSESSMENT_NUMBER = "+18054398008"


class ConfigError(ValueError):
    """Raised when local configuration is missing or unsafe."""


def _normalize_phone(value: str) -> str:
    return "".join(ch for ch in value.strip() if ch == "+" or ch.isdigit())


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from_number: str
    target_phone_number: str
    public_base_url: str
    openai_api_key: str
    openai_realtime_model: str
    openai_transcription_model: str
    openai_analysis_model: str
    call_recordings_dir: Path
    call_transcripts_dir: Path
    call_reports_dir: Path
    log_level: str

    @property
    def twiml_url(self) -> str:
        return f"{self.public_base_url.rstrip('/')}/voice/twiml"

    @property
    def media_stream_url(self) -> str:
        base = self.public_base_url.rstrip("/")
        if base.startswith("https://"):
            return "wss://" + base.removeprefix("https://") + "/voice/media"
        if base.startswith("http://"):
            return "ws://" + base.removeprefix("http://") + "/voice/media"
        return f"wss://{base}/voice/media"


def load_settings(require_public_url: bool = True) -> Settings:
    load_dotenv()

    target_phone_number = _normalize_phone(os.getenv("TARGET_PHONE_NUMBER", ASSESSMENT_NUMBER))
    if target_phone_number != ASSESSMENT_NUMBER:
        raise ConfigError(
            f"Unsafe TARGET_PHONE_NUMBER={target_phone_number}. "
            f"This challenge must call only {ASSESSMENT_NUMBER}."
        )

    public_base_url = os.getenv("PUBLIC_BASE_URL", "").strip()
    if require_public_url and (not public_base_url or "example" in public_base_url):
        raise ConfigError("Set PUBLIC_BASE_URL to your HTTPS tunnel URL before placing calls.")

    return Settings(
        twilio_account_sid=_required("TWILIO_ACCOUNT_SID"),
        twilio_auth_token=_required("TWILIO_AUTH_TOKEN"),
        twilio_from_number=_normalize_phone(_required("TWILIO_FROM_NUMBER")),
        target_phone_number=target_phone_number,
        public_base_url=public_base_url,
        openai_api_key=_required("OPENAI_API_KEY"),
        openai_realtime_model=os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-2").strip(),
        openai_transcription_model=os.getenv("OPENAI_TRANSCRIPTION_MODEL", "gpt-realtime-whisper").strip(),
        openai_analysis_model=os.getenv("OPENAI_ANALYSIS_MODEL", "gpt-5.4-mini").strip(),
        call_recordings_dir=Path(os.getenv("CALL_RECORDINGS_DIR", "data/recordings")),
        call_transcripts_dir=Path(os.getenv("CALL_TRANSCRIPTS_DIR", "data/transcripts")),
        call_reports_dir=Path(os.getenv("CALL_REPORTS_DIR", "data/reports")),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
    )


def masked(value: str, visible: int = 4) -> str:
    if len(value) <= visible:
        return "*" * len(value)
    return f"{'*' * (len(value) - visible)}{value[-visible:]}"

from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

from pretty_good_ai.config import ConfigError, load_settings
from pretty_good_ai.scenarios import get_scenario


TWILIO_RECORDING_EXTENSION = "mp3"
OPENAI_TRANSCRIPTION_URL = "https://api.openai.com/v1/audio/transcriptions"
REALTIME_TRANSCRIPTION_MODELS = {"gpt-realtime-whisper", "gpt-realtime-translate"}


def _call_id(call_number: str) -> str:
    value = call_number.strip().removeprefix("call-")
    return f"call-{int(value):02d}"


def _recording_path(call_number: str) -> Path:
    settings = load_settings(require_public_url=False)
    return settings.call_recordings_dir / f"{_call_id(call_number)}.{TWILIO_RECORDING_EXTENSION}"


def _transcript_path(call_number: str) -> Path:
    settings = load_settings(require_public_url=False)
    return settings.call_transcripts_dir / f"transcript-{int(call_number.strip().removeprefix('call-')):02d}.md"


def download_recording(call_number: str, call_sid: str, recording_sid: str) -> Path:
    settings = load_settings(require_public_url=False)
    settings.call_recordings_dir.mkdir(parents=True, exist_ok=True)
    output_path = _recording_path(call_number)
    url = (
        f"https://api.twilio.com/2010-04-01/Accounts/"
        f"{settings.twilio_account_sid}/Recordings/{recording_sid}.{TWILIO_RECORDING_EXTENSION}"
    )

    response = requests.get(
        url,
        auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        timeout=60,
    )
    response.raise_for_status()
    output_path.write_bytes(response.content)

    metadata_path = output_path.with_suffix(".json")
    metadata_path.write_text(
        json.dumps(
            {
                "call_number": _call_id(call_number),
                "call_sid": call_sid,
                "recording_sid": recording_sid,
                "source": "twilio",
                "format": TWILIO_RECORDING_EXTENSION,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved recording: {output_path}")
    print(f"Saved metadata: {metadata_path}")
    return output_path


def _transcription_model() -> str:
    settings = load_settings(require_public_url=False)
    model = settings.openai_transcription_model
    if model in REALTIME_TRANSCRIPTION_MODELS:
        return "gpt-4o-transcribe-diarize"
    return model


def transcribe_recording(call_number: str, scenario_id: str, model: str | None = None) -> Path:
    settings = load_settings(require_public_url=False)
    settings.call_transcripts_dir.mkdir(parents=True, exist_ok=True)
    audio_path = _recording_path(call_number)
    if not audio_path.exists():
        raise FileNotFoundError(f"Recording not found: {audio_path}")

    chosen_model = model or _transcription_model()
    scenario = get_scenario(scenario_id)

    with audio_path.open("rb") as audio_file:
        files = {
            "file": (audio_path.name, audio_file, "audio/mpeg"),
        }
        data = {
            "model": chosen_model,
            "response_format": "diarized_json" if chosen_model.endswith("diarize") else "text",
        }
        if chosen_model.endswith("diarize"):
            data["chunking_strategy"] = "auto"

        response = requests.post(
            OPENAI_TRANSCRIPTION_URL,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            data=data,
            files=files,
            timeout=240,
        )

    if response.status_code >= 400 and chosen_model.endswith("diarize"):
        print("Diarized transcription failed; falling back to gpt-4o-transcribe text output.")
        return transcribe_recording(call_number, scenario_id, model="gpt-4o-transcribe")

    response.raise_for_status()

    transcript_path = _transcript_path(call_number)
    raw_path = transcript_path.with_suffix(".json")

    if response.headers.get("content-type", "").startswith("application/json"):
        payload = response.json()
        raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        body = _format_json_transcript(payload)
    else:
        body = response.text.strip()

    transcript_path.write_text(
        "\n".join(
            [
                f"# Transcript {_call_id(call_number)}",
                "",
                f"- Scenario: {scenario.id} - {scenario.title}",
                f"- Recording: `{audio_path.as_posix()}`",
                f"- Transcription model: `{chosen_model}`",
                "",
                "## Transcript",
                "",
                body,
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Saved transcript: {transcript_path}")
    if raw_path.exists():
        print(f"Saved raw transcription JSON: {raw_path}")
    return transcript_path


def _format_json_transcript(payload: dict) -> str:
    segments = payload.get("segments") or payload.get("diarization") or payload.get("speaker_segments")
    if isinstance(segments, list) and segments:
        merged = _merge_segments(segments)
        patient_speaker = _infer_patient_speaker(merged)
        lines: list[str] = []
        for segment in merged:
            speaker = _speaker_name(segment.get("speaker"), patient_speaker)
            text = (segment.get("text") or "").strip()
            start = segment.get("start")
            if text:
                prefix = f"[{_format_time(start)}] " if isinstance(start, (int, float)) else ""
                lines.append(f"{prefix}**{speaker}:** {text}")
        if lines:
            return "\n\n".join(lines)

    text = payload.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()
    return "```json\n" + json.dumps(payload, indent=2) + "\n```"


def _merge_segments(segments: list[dict]) -> list[dict]:
    merged: list[dict] = []
    for segment in segments:
        text = (segment.get("text") or "").strip()
        if not text:
            continue
        speaker = segment.get("speaker") or segment.get("speaker_label") or "Speaker"
        start = segment.get("start")
        end = segment.get("end")

        previous = merged[-1] if merged else None
        previous_end = previous.get("end") if previous else None
        close_gap = (
            isinstance(start, (int, float))
            and isinstance(previous_end, (int, float))
            and start - previous_end <= 1.25
        )
        if previous and previous.get("speaker") == speaker and close_gap:
            previous["text"] = _join_text(previous["text"], text)
            previous["end"] = end
        else:
            merged.append({"speaker": speaker, "text": text, "start": start, "end": end})
    return merged


def _join_text(left: str, right: str) -> str:
    if not left:
        return right
    if right[:1] in {".", ",", "?", "!", ":", ";"}:
        return left.rstrip() + right
    return f"{left.rstrip()} {right.lstrip()}"


def _infer_patient_speaker(segments: list[dict]) -> str | None:
    scores: dict[str, int] = {}
    patient_markers = (" i ", " i'm ", " i'd ", " my ", " me ", " knee ", " appointment ", " soccer ")
    for segment in segments:
        speaker = str(segment.get("speaker", ""))
        text = f" {str(segment.get('text', '')).lower()} "
        scores.setdefault(speaker, 0)
        scores[speaker] += sum(marker in text for marker in patient_markers)
    if not scores:
        return None
    speaker, score = max(scores.items(), key=lambda item: item[1])
    return speaker if score > 0 else None


def _speaker_name(speaker: str | None, patient_speaker: str | None) -> str:
    if speaker and speaker == patient_speaker:
        return "Patient"
    if speaker:
        return "Agent/Clinic"
    return "Speaker"


def _format_time(seconds: float) -> str:
    whole = int(seconds)
    return f"{whole // 60:02d}:{whole % 60:02d}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and transcribe call artifacts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download")
    download.add_argument("--call-number", required=True)
    download.add_argument("--call-sid", required=True)
    download.add_argument("--recording-sid", required=True)

    transcribe = subparsers.add_parser("transcribe")
    transcribe.add_argument("--call-number", required=True)
    transcribe.add_argument("--scenario-id", default="call-01")
    transcribe.add_argument("--model")

    all_command = subparsers.add_parser("all")
    all_command.add_argument("--call-number", required=True)
    all_command.add_argument("--call-sid", required=True)
    all_command.add_argument("--recording-sid", required=True)
    all_command.add_argument("--scenario-id", default="call-01")
    all_command.add_argument("--model")

    args = parser.parse_args()

    try:
        if args.command == "download":
            download_recording(args.call_number, args.call_sid, args.recording_sid)
        elif args.command == "transcribe":
            transcribe_recording(args.call_number, args.scenario_id, args.model)
        elif args.command == "all":
            download_recording(args.call_number, args.call_sid, args.recording_sid)
            transcribe_recording(args.call_number, args.scenario_id, args.model)
        return 0
    except (ConfigError, FileNotFoundError, requests.HTTPError) as exc:
        print(f"Artifact error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

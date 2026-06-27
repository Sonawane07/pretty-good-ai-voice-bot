from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests
from twilio.rest import Client

from pretty_good_ai.artifacts import download_recording, transcribe_recording
from pretty_good_ai.call_runner import place_call
from pretty_good_ai.config import ConfigError, load_settings
from pretty_good_ai.scenarios import get_scenario


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
TERMINAL_CALL_STATUSES = {"completed", "failed", "busy", "no-answer", "canceled"}
TERMINAL_RECORDING_STATUSES = {"completed", "absent", "deleted"}


def run_scenario(
    call_number: str,
    scenario_id: str,
    poll_interval_seconds: int,
    timeout_minutes: int,
    draft_bugs: bool,
) -> int:
    settings = load_settings(require_public_url=True)
    scenario = get_scenario(scenario_id)
    verify_running_server_scenario(settings.public_base_url, scenario)

    print(f"Running {call_label(call_number)}: {scenario.id} - {scenario.title}")
    call_sid = place_call(scenario_id=scenario_id, dry_run=False)
    if not call_sid:
        raise RuntimeError("Call did not return a Twilio SID.")

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    call = wait_for_call(client, call_sid, poll_interval_seconds, timeout_minutes)
    if call.status != "completed":
        print(f"Call ended with status={call.status}. Artifacts may be incomplete.")

    recording_sid = wait_for_recording(client, call_sid, poll_interval_seconds, timeout_minutes=3)
    if not recording_sid:
        print("No completed recording found. Skipping artifact download and transcription.")
        return 2

    download_recording(call_number=call_number, call_sid=call_sid, recording_sid=recording_sid)
    transcript_path = transcribe_recording(call_number=call_number, scenario_id=scenario_id)
    update_call_index(call_number, scenario_id, call_sid, recording_sid, call.status, transcript_path)

    if draft_bugs:
        draft_path = draft_bug_candidates(call_number, scenario_id, transcript_path)
        append_bug_report_draft(call_number, draft_path)

    print("Workflow complete.")
    print(f"Call SID: {call_sid}")
    print(f"Recording SID: {recording_sid}")
    print(f"Transcript: {transcript_path}")
    return 0


def verify_running_server_scenario(public_base_url: str, scenario) -> None:
    url = f"{public_base_url.rstrip('/')}/scenario/{scenario.id}"
    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException as exc:
        raise ConfigError(
            "Could not verify the running server scenario before placing the call. "
            "Make sure Uvicorn is running and ngrok points to it."
        ) from exc

    if response.status_code != 200:
        raise ConfigError(
            f"Running server did not expose scenario preflight endpoint ({response.status_code}). "
            "Restart Uvicorn so it loads the latest code before placing another paid call."
        )

    remote = response.json()
    mismatches = []
    for field in ("title", "goal", "details", "edge_case"):
        if (remote.get(field) or "") != (getattr(scenario, field) or ""):
            mismatches.append(field)

    if mismatches:
        raise ConfigError(
            "Running server scenario does not match local scenario "
            f"for {scenario.id}; mismatched fields: {', '.join(mismatches)}. "
            "Restart Uvicorn before placing another paid call."
        )

    print(f"Server scenario preflight OK: {scenario.id} - {scenario.title}")


def wait_for_call(client: Client, call_sid: str, poll_interval_seconds: int, timeout_minutes: int):
    deadline = time.monotonic() + timeout_minutes * 60
    while True:
        call = client.calls(call_sid).fetch()
        print(f"Call status: {call.status}")
        if call.status in TERMINAL_CALL_STATUSES:
            return call
        if time.monotonic() > deadline:
            raise TimeoutError(f"Timed out waiting for call {call_sid} to complete.")
        time.sleep(poll_interval_seconds)


def wait_for_recording(
    client: Client,
    call_sid: str,
    poll_interval_seconds: int,
    timeout_minutes: int,
) -> str | None:
    deadline = time.monotonic() + timeout_minutes * 60
    while True:
        recordings = client.recordings.list(call_sid=call_sid, limit=20)
        if recordings:
            recording = recordings[0]
            print(f"Recording status: {recording.status} ({recording.sid})")
            if recording.status == "completed":
                return recording.sid
            if recording.status in TERMINAL_RECORDING_STATUSES:
                return None
        else:
            print("Recording status: waiting")

        if time.monotonic() > deadline:
            return None
        time.sleep(poll_interval_seconds)


def update_call_index(
    call_number: str,
    scenario_id: str,
    call_sid: str,
    recording_sid: str,
    call_status: str,
    transcript_path: Path,
) -> None:
    settings = load_settings(require_public_url=False)
    scenario = get_scenario(scenario_id)
    settings.call_reports_dir.mkdir(parents=True, exist_ok=True)
    path = settings.call_reports_dir / "call-index.md"
    call = call_label(call_number)

    existing = path.read_text(encoding="utf-8") if path.exists() else "# Call Artifact Index\n"
    section = "\n".join(
        [
            f"\n## {call} - {scenario.title}",
            "",
            f"- Call SID: `{call_sid}`",
            f"- Recording SID: `{recording_sid}`",
            f"- Recording: `data/recordings/{call}.mp3`",
            f"- Transcript: `{transcript_path.as_posix()}`",
            f"- Raw transcription JSON: `data/transcripts/transcript-{call_number_value(call_number):02d}.json`",
            f"- Metadata: `data/recordings/{call}.json`",
            f"- Twilio status: `{call_status}`",
            "- Review status: Needs user review before marking final.",
            "",
        ]
    )
    path.write_text(_replace_or_append_section(existing, f"## {call} - ", section), encoding="utf-8")
    print(f"Updated call index: {path}")


def draft_bug_candidates(call_number: str, scenario_id: str, transcript_path: Path) -> Path:
    settings = load_settings(require_public_url=False)
    scenario = get_scenario(scenario_id)
    transcript = transcript_path.read_text(encoding="utf-8")
    output_path = settings.call_reports_dir / f"bug-candidates-{call_label(call_number)}.md"

    prompt = f"""
Analyze this Pretty Good AI challenge phone-call transcript.

Scenario:
- ID: {scenario.id}
- Title: {scenario.title}
- Goal: {scenario.goal}
- Details: {scenario.details}
- Edge case: {scenario.edge_case or "None"}

Return concise Markdown with:
1. Call outcome in 2-4 bullets.
2. Candidate bugs, if any. For each: title, severity, timestamp, what happened, why it matters, expected behavior.
3. Items to exclude because they are likely caller-bot issues, transcription noise, or expected persistent state.

Be conservative. Do not invent bugs. If there are no strong candidates, say so.

Transcript:
{transcript}
""".strip()

    response = requests.post(
        OPENAI_RESPONSES_URL,
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.openai_analysis_model,
            "instructions": "You are a careful QA analyst for healthcare voice-agent testing.",
            "input": prompt,
        },
        timeout=180,
    )

    if response.status_code >= 400:
        output_path.write_text(
            "\n".join(
                [
                    f"# Bug Candidates {call_label(call_number)}",
                    "",
                    "Automatic bug drafting failed.",
                    "",
                    f"- Status code: {response.status_code}",
                    f"- Response: `{response.text[:1000]}`",
                    "",
                    "Review the transcript manually.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        print(f"Saved failed bug-draft note: {output_path}")
        return output_path

    text = extract_response_text(response.json())
    output_path.write_text(
        "\n".join(
            [
                f"# Bug Candidates {call_label(call_number)}",
                "",
                "> Review required before copying any finding into the final bug report.",
                "",
                text.strip(),
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Saved bug candidates: {output_path}")
    return output_path


def extract_response_text(payload: dict) -> str:
    texts: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                texts.append(content["text"])
    return "\n\n".join(texts) if texts else json.dumps(payload, indent=2)


def append_bug_report_draft(call_number: str, draft_path: Path) -> None:
    settings = load_settings(require_public_url=False)
    path = settings.call_reports_dir / "bug-report.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Bug Report\n"
    call = call_label(call_number)
    section = "\n".join(
        [
            f"\n## {call}",
            "",
            f"Draft bug candidates were generated at `{draft_path.as_posix()}`.",
            "",
            "Review this draft before moving findings into the final bug report.",
            "",
        ]
    )
    path.write_text(_replace_or_append_section(existing, f"## {call}", section), encoding="utf-8")
    print(f"Updated bug report draft pointer: {path}")


def _replace_or_append_section(existing: str, heading_prefix: str, new_section: str) -> str:
    lines = existing.rstrip().splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(heading_prefix)), None)
    if start is None:
        return existing.rstrip() + "\n" + new_section

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[:start] + new_section.strip("\n").splitlines() + lines[end:]) + "\n"


def call_label(call_number: str) -> str:
    return f"call-{call_number_value(call_number):02d}"


def call_number_value(call_number: str) -> int:
    value = call_number.strip().removeprefix("call-")
    return int(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one full Pretty Good AI challenge call workflow")
    parser.add_argument("--call-number", required=True, help="Call number, such as 02.")
    parser.add_argument("--scenario-id", required=True, help="Scenario id, such as call-02.")
    parser.add_argument("--poll-interval-seconds", type=int, default=10)
    parser.add_argument("--timeout-minutes", type=int, default=8)
    parser.add_argument("--no-bug-draft", action="store_true", help="Skip automatic bug candidate drafting.")
    args = parser.parse_args()

    try:
        return run_scenario(
            call_number=args.call_number,
            scenario_id=args.scenario_id,
            poll_interval_seconds=args.poll_interval_seconds,
            timeout_minutes=args.timeout_minutes,
            draft_bugs=not args.no_bug_draft,
        )
    except (ConfigError, KeyError, RuntimeError, TimeoutError, requests.HTTPError) as exc:
        print(f"Workflow error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

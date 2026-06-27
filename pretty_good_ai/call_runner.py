from __future__ import annotations

import argparse
from datetime import UTC, datetime

from twilio.rest import Client

from pretty_good_ai.config import ConfigError, load_settings, masked
from pretty_good_ai.scenarios import get_scenario


def _print_config_summary() -> None:
    settings = load_settings(require_public_url=False)
    print("Configuration OK")
    print(f"Twilio SID: {masked(settings.twilio_account_sid)}")
    print(f"Twilio from: {settings.twilio_from_number}")
    print(f"Target: {settings.target_phone_number}")
    if settings.public_base_url and "example" not in settings.public_base_url:
        print(f"Webhook: {settings.twiml_url}")
        print(f"Media stream: {settings.media_stream_url}")
    else:
        print("Webhook: not ready - set PUBLIC_BASE_URL after starting an HTTPS tunnel")
        print("Media stream: not ready - set PUBLIC_BASE_URL after starting an HTTPS tunnel")
    print(f"OpenAI realtime model: {settings.openai_realtime_model}")
    print(f"OpenAI transcription model: {settings.openai_transcription_model}")


def place_call(scenario_id: str, dry_run: bool) -> str | None:
    settings = load_settings(require_public_url=not dry_run)
    scenario = get_scenario(scenario_id)
    started_at = datetime.now(UTC).isoformat()

    twiml_url = (
        settings.twiml_url
        if settings.public_base_url and "example" not in settings.public_base_url
        else "not ready - set PUBLIC_BASE_URL after starting an HTTPS tunnel"
    )

    print(f"Scenario: {scenario.id} - {scenario.title}")
    print(f"From: {settings.twilio_from_number}")
    print(f"To: {settings.target_phone_number}")
    print(f"TwiML webhook: {twiml_url}")
    print(f"Started at: {started_at}")

    if dry_run:
        print("Dry run only. No call was placed.")
        return None

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    call = client.calls.create(
        to=settings.target_phone_number,
        from_=settings.twilio_from_number,
        url=f"{settings.twiml_url}?scenario_id={scenario.id}",
        record=True,
        recording_channels="dual",
        recording_status_callback=f"{settings.public_base_url.rstrip('/')}/voice/recording-status",
        recording_status_callback_method="POST",
    )
    print(f"Call placed. Twilio call SID: {call.sid}")
    return call.sid


def main() -> int:
    parser = argparse.ArgumentParser(description="Pretty Good AI challenge call runner")
    parser.add_argument("--check", action="store_true", help="Validate configuration without placing a call.")
    parser.add_argument("--dry-run", action="store_true", help="Preview a call without placing it.")
    parser.add_argument("--place-call", action="store_true", help="Place a real call to the assessment number.")
    parser.add_argument("--scenario-id", default="call-01", help="Scenario id to run, such as call-01.")
    args = parser.parse_args()

    try:
        if args.check:
            _print_config_summary()
            return 0

        if args.place_call and args.dry_run:
            raise ConfigError("Use either --place-call or --dry-run, not both.")

        place_call(scenario_id=args.scenario_id, dry_run=not args.place_call)
        return 0
    except (ConfigError, KeyError) as exc:
        print(f"Configuration error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

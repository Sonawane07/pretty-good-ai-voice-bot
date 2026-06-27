from __future__ import annotations

import argparse

from twilio.rest import Client

from pretty_good_ai.config import ConfigError, load_settings


def show_call_status(call_sid: str) -> None:
    settings = load_settings(require_public_url=False)
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    call = client.calls(call_sid).fetch()

    print(f"Call SID: {call.sid}")
    print(f"Status: {call.status}")
    print(f"From: {_field(call, 'from')}")
    print(f"To: {call.to}")
    print(f"Start time: {call.start_time}")
    print(f"End time: {call.end_time}")
    print(f"Duration seconds: {call.duration}")
    print(f"Price: {call.price} {call.price_unit}")

    recordings = client.recordings.list(call_sid=call_sid, limit=20)
    print(f"Recordings: {len(recordings)}")
    for recording in recordings:
        print(f"- {recording.sid} status={recording.status} duration={recording.duration}s channels={recording.channels}")


def _field(instance, name: str, default: str = "") -> str:
    value = getattr(instance, name, None)
    if value is not None:
        return str(value)
    properties = getattr(instance, "_properties", {}) or {}
    return str(properties.get(name, default))


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a Twilio call and its recordings")
    parser.add_argument("call_sid", help="Twilio call SID, such as CA...")
    args = parser.parse_args()

    try:
        show_call_status(args.call_sid)
        return 0
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse

from twilio.rest import Client

from pretty_good_ai.config import ConfigError, load_settings


def end_call(call_sid: str) -> None:
    settings = load_settings(require_public_url=False)
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    call = client.calls(call_sid).update(status="completed")
    print(f"Call {call.sid} updated to status={call.status}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Control a Twilio test call")
    parser.add_argument("call_sid", help="Twilio call SID, such as CA...")
    parser.add_argument("--end", action="store_true", help="End an active call.")
    args = parser.parse_args()

    if not args.end:
        print("No action requested. Use --end to end an active call.")
        return 2

    try:
        end_call(args.call_sid)
        return 0
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

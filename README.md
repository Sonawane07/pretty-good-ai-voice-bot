# Pretty Good AI Voice Bot

Python voice bot for the Pretty Good AI engineering challenge. The bot calls the assessment number, behaves like a realistic Pivot Point Orthopedics patient, records and transcribes both sides of each call, and produces review-ready bug reports.

## Submission Status

- 10 completed test calls: `call-01` through `call-10`
- MP3 recordings: `data/recordings/`
- Markdown transcripts and raw transcription JSON: `data/transcripts/`
- Final reviewed bug report: `data/reports/bug-report.md`
- Call artifact index: `data/reports/call-index.md`
- Architecture notes: `architecture.md`

Best findings to review first:

- `call-04`: appointment confirmed in one call was not retrievable later
- `call-02`: existing knee appointment was treated as a shoulder follow-up without verification
- `call-03`: afternoon slot was offered as the earliest weekday morning appointment

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill `.env` with local credentials. Do not commit `.env`.

Required values:

```env
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
TARGET_PHONE_NUMBER=+18054398008
PUBLIC_BASE_URL=https://your-tunnel-url.example
OPENAI_API_KEY=
OPENAI_REALTIME_MODEL=gpt-realtime-2
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-transcribe-diarize
OPENAI_ANALYSIS_MODEL=gpt-5.4-mini
```

## Run

Start the local webhook server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn pretty_good_ai.server:app --host 127.0.0.1 --port 8080
```

Expose port `8080` with an HTTPS tunnel, then set `PUBLIC_BASE_URL` in `.env` to that tunnel URL.

Validate configuration without making a call:

```powershell
.\.venv\Scripts\python.exe -m pretty_good_ai.call_runner --check
```

Preview a scenario without placing a call:

```powershell
.\.venv\Scripts\python.exe -m pretty_good_ai.call_runner --dry-run --scenario-id call-10
```

Run a full scenario workflow:

```powershell
.\.venv\Scripts\python.exe -m pretty_good_ai.run_scenario --call-number 10 --scenario-id call-10
```

The workflow places the call, waits for completion, finds the Twilio recording, downloads it, transcribes it, updates `data/reports/call-index.md`, and drafts bug candidates.

Important: restart Uvicorn after changing scenarios. The workflow preflights the running server scenario and refuses to place a paid call if the server has stale scenario text.

## Safety

All assessment calls must go only to:

```text
+1-805-439-8008
```

The code validates the target number before placing a call. Do not call the number shown in the Pretty Good AI product confirmation screen.

Use one caller phone number for the full submission; the tested Twilio caller number is recorded in the submission form in E.164 format.

## Artifacts

Each call has:

- `data/recordings/call-XX.mp3`
- `data/recordings/call-XX.json`
- `data/transcripts/transcript-XX.md`
- `data/transcripts/transcript-XX.json`

The final bug report is `data/reports/bug-report.md`.

# Challenge Execution Schedule

## Phase 1 - Understand And Set Up

Estimated time: 45-60 minutes

- Create a test account at `pgai.us/athena` to understand the patient experience.
- Do not call the number shown in that product flow.
- Confirm the only target number is `+1-805-439-8008`.
- Use Twilio for telephony and recordings.
- Use OpenAI Realtime for the live patient voice bot.
- Use OpenAI transcription and text models for transcripts and bug analysis.
- Create `.env.example` with required secrets and phone settings.

## Phase 2 - Build The Minimal Calling Loop

Estimated time: 1.5-2.5 hours

- Create the Python project structure.
- Implement configuration loading and target-number validation.
- Place a test call through the telephony provider.
- Connect Twilio call audio to the OpenAI Realtime session.
- Record the call.
- Save call metadata locally.
- Confirm the recording can be downloaded.

## Phase 3 - Build Patient Simulation

Estimated time: 1.5-2 hours

- Define 10 patient scenarios.
- Add scenario goals, patient profile details, and escalation/exit conditions.
- Implement the voice bot prompt and conversation state handling.
- Tune for natural pacing, sensible turn-taking, and active steering.

## Phase 4 - Transcription And Artifact Pipeline

Estimated time: 1-1.5 hours

- Transcribe each recording.
- Save transcripts with both sides when available.
- Use consistent artifact names:
  - `data/recordings/call-01.mp3`
  - `data/transcripts/transcript-01.md`
  - `data/reports/bug-report.md`
- Add a command to run post-call processing.

## Phase 5 - First Iteration Calls

Estimated time: 1-1.5 hours

- Run 2-3 early calls.
- Listen to recordings.
- Check for latency, awkward pauses, interruptions, and bot confusion.
- Improve prompts and scenario logic based on observed failures.
- Record notes showing iteration.

## Phase 6 - Final 10 Calls

Estimated time: 1.5-2.5 hours

- Run at least 10 complete calls.
- Ensure each call is a full conversation, usually 1-3 minutes.
- Confirm every call has:
  - Recording.
  - Transcript.
  - Scenario label.
  - Notes about outcome and possible bug.

## Phase 7 - Bug Report And Documentation

Estimated time: 1-1.5 hours

- Review transcripts and recordings.
- Select meaningful issues, not punctuation or wording nitpicks.
- Write `data/reports/bug-report.md`.
- Add or update:
  - `README.md`
  - Architecture section or `architecture.md`
  - Setup instructions
  - Run command
  - Artifact index

## Phase 8 - Loom And Submission

Estimated time: 45-60 minutes

- Record a Loom walkthrough under 5 minutes.
- Include:
  - What the bot does.
  - Architecture and key design decisions.
  - Example call output.
  - Best bugs found.
  - What changed after iteration.
- Record the required 5-minute screen capture of AI-assisted debugging.
- Push the public GitHub repository.
- Submit the form with:
  - GitHub repository link.
  - Loom walkthrough link.
  - One caller phone number in E.164 format.

## Proposed 10-Call Scenario Set

1. New orthopedic patient schedules a visit for knee pain.
2. Existing patient reschedules a shoulder follow-up appointment.
3. Patient cancels and asks about cancellation policy.
4. Post-procedure medication refill request with low urgency.
5. Medication refill request with missing pharmacy details.
6. Patient asks about office hours and weekend availability.
7. Patient asks about location, parking, and directions.
8. Patient asks whether a specific insurance is accepted.
9. Patient gives unclear back-pain symptoms and changes their mind mid-call.
10. Patient interrupts the agent and asks an unrelated question.

## Quality Gate Before Submission

- At least 10 complete calls exist.
- Audio files are playable.
- Transcripts are readable and matched to recordings.
- The bot sounds like a real patient, not a rigid benchmark script.
- Bug report references exact calls and timestamps.
- README can take a reviewer from setup to running the bot.
- No secrets are committed.

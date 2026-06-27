# Pretty Good AI Voice Bot Challenge PRD

## Objective

Build a Python voice bot that calls Pretty Good AI's assessment line and behaves like a realistic patient. The bot should run at least 10 full voice conversations, record and transcribe both sides, then help identify useful bugs or quality issues in the target AI agent.

## Assessment Phone Number

All calls must go only to:

`+1-805-439-8008`

The bot must not call the phone number shown in the pgai.us/athena product flow.

## Success Criteria

The submission succeeds if it demonstrates:

- Coherent, natural voice conversations with the target agent.
- Working Python code that makes real phone calls.
- At least 10 complete calls, typically 1-3 minutes each.
- Audio recordings in `ogg` or `mp3` format.
- Transcripts that include both sides of each conversation.
- A bug report with useful findings and references to specific calls/timestamps.
- Clear setup instructions, architecture notes, and a short Loom walkthrough.
- Evidence of iteration after listening to early calls.

## Primary Users

- Challenge reviewer: listens to calls first, then reviews code and documents.
- Candidate/developer: runs the bot, reviews outputs, tunes scenarios, and submits the final package.

## Core Requirements

### Voice Calling

- The system must call only `+1-805-439-8008`.
- All calls must originate from one consistent E.164 phone number.
- The bot must speak naturally enough to sustain a lucid conversation.
- The bot should steer conversations toward a test-case outcome instead of passively chatting.

### Patient Simulation

The bot should cover at least these scenario types:

- Simple appointment scheduling.
- Rescheduling or canceling an appointment.
- Medication refill request.
- Office hours, location, and insurance questions.
- Edge cases such as interruptions, unclear requests, odd constraints, and unusual patient behavior.

### Recording And Transcription

- Save every call recording as `ogg` or `mp3`.
- Generate a transcript for every call.
- Preserve both sides of the conversation.
- Store outputs with stable names, such as `call-01.mp3` and `transcript-01.md`.

### Analysis And Bug Reporting

- Review call outputs for bugs and quality issues.
- Prioritize meaningful product issues over minor wording problems.
- Each bug should include:
  - Title.
  - Severity.
  - Call reference.
  - Timestamp or transcript excerpt location.
  - What happened.
  - Why it is a problem.
  - Expected behavior.

## Selected Technical Approach

Use Twilio to place calls, record audio, and connect the phone call to a real-time voice bot. Use OpenAI's Realtime API for the live patient conversation because the challenge prioritizes lucid, natural voice interaction before code review. Use OpenAI transcription or post-call analysis models to produce transcripts and summarize likely bugs.

The simplest robust architecture is:

1. Python app starts a call through Twilio.
2. Twilio connects the call audio to our app over a media stream or hosted webhook.
3. OpenAI Realtime listens to the agent, tracks the scenario state, and responds as a realistic Pivot Point Orthopedics patient.
4. The call is recorded.
5. After each call, the system downloads the recording, transcribes it, and saves artifacts.
6. A review script or manual review pass turns transcripts into a bug report.

## Suggested Repository Structure

```text
.
├── README.md
├── prd.md
├── schedule.md
├── .env.example
├── src/
│   ├── config.py
│   ├── call_runner.py
│   ├── voice_bot.py
│   ├── scenarios.py
│   ├── transcription.py
│   └── bug_analysis.py
├── data/
│   ├── recordings/
│   ├── transcripts/
│   └── reports/
└── tests/
```

## Environment Variables

The final app should document variables like:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`
- `OPENAI_API_KEY`
- `OPENAI_REALTIME_MODEL`
- `OPENAI_TRANSCRIPTION_MODEL`
- `TARGET_PHONE_NUMBER`

`TARGET_PHONE_NUMBER` should default to, or be validated against, `+1-805-439-8008` to prevent accidental calls elsewhere.

## Demo Clinic Context

The setup flow shows the demo clinic as Pivot Point Orthopedics. It mentions patient tasks such as creating or changing appointments, updating insurance, and refilling prescriptions. Test scenarios should sound like orthopedic patient calls, such as knee pain, shoulder injury, back pain, physical therapy questions, post-procedure medication refills, insurance updates, and appointment changes.

## Deliverables Checklist

- Working Python voice bot.
- `README.md` with setup and run instructions.
- `.env.example` with required variables.
- Architecture document or section.
- Minimum 10 call recordings.
- Minimum 10 matching transcripts.
- Bug report.
- Loom walkthrough, max 5 minutes.
- 5-minute screen recording showing AI-assisted debugging and iteration.
- Public GitHub repository link.
- Submission form completed with GitHub link, Loom link, and one calling number in E.164 format.

## Risks And Mitigations

- Poor conversation quality: start with a small scenario set, listen to early calls, and tune prompts before running all 10.
- Latency or awkward pauses: keep prompts concise, use streaming where possible, and avoid overlong reasoning in the live loop.
- Accidental wrong-number calls: hard-code validation for the assessment number.
- Missing both-side transcripts: verify recording and transcription output after the first successful call.
- Weak bug findings: design scenarios that probe realistic failure modes, such as closed days, refill authorization, insurance ambiguity, and conflicting patient details.

## Non-Goals

- Production-grade infrastructure.
- Complex dashboards.
- Large-scale load testing.
- Perfect code polish.
- Fancy diagrams or visual-heavy documentation.

# Bug Candidates call-04

> Review required before copying any finding into the final bug report.

## 1. Call outcome

- The caller asked for the appointment currently on file before trying to add lower back pain to the same visit.
- In the prior call, the agent had confirmed a new appointment for Tuesday, July 7 at 10:30 a.m. with Dr. Doogie Hauser.
- Based on audio review, the agent indicated there was no appointment scheduled / no open appointment on file.
- The scripted trap about "two appointments" was not reached because the call ended early.

## 2. Candidate bug

### Appointment confirmed in one call was not retrievable in the next call

- Severity: High
- Timestamp: 00:34-01:07

What happened: In `call-03`, the agent confirmed a new appointment for Tuesday, July 7 at 10:30 a.m. with Dr. Doogie Hauser. In `call-04`, the same verified patient asked what appointment was currently on file. Based on audio review, the agent indicated there was no appointment scheduled / no open appointment on file.

Why it matters: This is an appointment persistence/retrieval issue, not a general memory issue. If a booking is confirmed in one call but cannot be retrieved in the next call, patients may believe they are scheduled when the system did not retain the appointment.

Expected behavior: The appointment should be persisted and retrievable in later calls for the same verified patient. If demo state does not persist, the agent should clearly explain that instead of confirming a booking as if it will remain on file.

## 3. Items to exclude

- The DOB mismatch message is likely expected demo behavior, not a bug.
- The transcript contains obvious ASR artifacts around 01:02-01:07; this candidate relies on audio review confirming that the agent said no appointment was scheduled.
- Do not report a separate bug about adding lower back pain to the visit; the call ended before that flow was meaningfully tested.
- The caller ending the call early appears to be script behavior, not an agent issue.
- The "two appointments" trap was not exercised, so do not infer a bug about confirming two appointments from this transcript.

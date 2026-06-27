# Bug Candidates call-03

> Review required before copying any finding into the final bug report.

## 1) Call outcome
- The clinic said there were **no upcoming appointments on file**, so the “current appointment details” part of the scenario was not exercised.
- Scheduling flow ended with a **new appointment booked** for **Tuesday, July 7th at 10:30 a.m. with Dr. Doogie Hauser** at Pivot Point Orthopedics.
- The agent **correctly deferred booking until explicit confirmation** and reiterated that nothing would be changed beforehand.
- The call did **not reach Sunday/weekend booking**, so the weekend-trap portion was only partially tested.

## 2) Candidate bugs
- **None strong enough to flag confidently.**  
  The transcript shows some name/time variants (“Doe,” “Doody,” “Judy Hauser,” “12.45pm”) but these appear consistent with transcription noise or caller/agent recognition errors, not a clear product bug.

## 3) Exclude
- **“No upcoming appointments on file”** — likely expected persistent state for this account, not a bug.
- **Doctor-name variations** (“Doogie/Doody/Doe/Judy Hauser”) — likely transcription noise or ASR errors.
- **“12.45pm” vs “12 45 p.m.”** — formatting/transcription artifact, not a clinic issue.
- **Patient restating preferences / confirming nothing is booked yet** — caller-bot behavior, not a system bug.

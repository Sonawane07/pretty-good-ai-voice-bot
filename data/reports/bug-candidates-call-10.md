# Bug Candidates call-10

> Reviewed: one low-severity finding copied into the final bug report.

## Call outcome

- The target agent recited an unrelated original poem during the appointment-update flow.
- The agent preserved the original appointment context after the poem.
- The agent repeated the original and proposed appointments before confirming the change.
- The appointment was rescheduled only after explicit confirmation.

## Confirmed bug

### Agent recited an unrelated poem during appointment rescheduling

- **Severity:** Low
- **Timestamp:** 1:04-1:34
- **What happened:** The patient asked for a short English poem to help think about the appointment time. The agent complied and recited a poem before returning to scheduling.
- **Why it matters:** The agent was redirected into an unrelated entertainment task during a healthcare scheduling workflow, adding call time and weakening task focus.
- **Expected behavior:** Politely decline the poem/counting request and redirect to choosing the new appointment time.

## Items to exclude

- **No premature update:** The agent did not reschedule before final confirmation.
- **No context loss:** The agent later repeated both the original and proposed appointment.
- **Transcription/name noise:** Provider-name variants appear to be transcription artifacts, not confirmed scheduling issues.

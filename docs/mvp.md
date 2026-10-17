# harwatch hosted watch — MVP delivery process (manual fulfillment)

Locked spec: $29/month, 1 API, 1 baseline, up to 30 checks/month of
customer-submitted HARs, Slack/email notice on break, GOLD receipt per
check, email support, cancel anytime. MVP = scheduled CHECK (not
re-record). No direct API hits, no dashboard, no multi-API, no 24/7
polling, no credential storage.

## Flow

1. **Waitlist** — customer emails with subject `harwatch watch - [API name]`.
   No checkout until delivery exists. Payment Link is unverified; do not use.
2. **Intake** (see intake.md) — collect API name, endpoint URL (reference
   only, NOT hit in MVP), contact email, optional Slack webhook, baseline
   HAR, fields to watch. No credentials. Warn on Authorization header.
3. **Freeze baseline** — operator runs `harwatch freeze baseline.har --out
   baseline.json`. Store the baseline contract + its SHA256. Delete the
   baseline HAR after freezing (never store customer recordings).
4. **Check** — customer submits a new HAR. Operator runs:
   `python -m harwatch.runner baseline.json submitted.har --out receipt.json`
   Delete the submitted HAR after the check. Never store it.
5. **Notice + receipt** (see notice.md) — send notice (Slack/email) + GOLD
   receipt. On PASS: receipt only. On FAIL: notice + receipt with breaks.
6. **Cancel** — stop future charges, stop checks. Refund that month if we
   failed to run a submitted check. No refund for months with no submissions
   (check requires submission).

## Operator rules

- Never store a customer HAR, baseline HAR, or any secret. Contracts
  (baseline.json) contain shapes only, no header values, no secret query
  params — safe to store.
- If a submitted HAR contains an Authorization / Cookie / API-key header
  or a secret query param, warn the customer to redact and re-send.
  Do not store the secret.
- Every check produces a GOLD receipt. No check without a receipt.
- No uptime claim, no fake numbers. Receipt reports only what ran.

# harwatch intake — waitlist + intake email templates

## Waitlist (until delivery exists)

Customer emails with subject: `harwatch watch - [API name]`

Reply: confirm waitlist, restate the offer (see below), ask for intake
details when ready. No checkout link until delivery exists.

## Offer text (use verbatim)

harwatch hosted watch — $29/month, 1 API.

- 1 frozen baseline from your recording.
- Up to 30 checks/month. You submit a new recording (HAR); we check it
  against your frozen baseline and notify you if a field breaks.
- Slack/email notice when a watched field breaks.
- GOLD receipt per check: baseline hash, submitted HAR hash, timestamp,
  fields checked (count), overall result, breaking changes listed, check ID.
- Email support, best-effort. Cancel anytime — stops future charges
  and checks.
- This is a scheduled CHECK of recordings you submit, not automatic
  re-recording. We do not hit your API. We do not store your recordings
  or any secrets.

## Intake email (after checkout)

Ask the customer for:

1. API name.
2. Endpoint URL (reference only — NOT hit in MVP).
3. Contact email.
4. Slack webhook URL (optional) — never email it to us. A webhook URL is a credential: you will set it in your own harwatch config at setup.
5. Baseline HAR file (one recording of the API).
6. Fields to watch (auto from baseline; customer may narrow).

## No credentials

Do NOT send API keys, tokens, passwords, or Slack webhook URLs. If your API needs auth,
redact / strip auth before sending the HAR. If a HAR contains an
Authorization header, we will warn you and will not store it.

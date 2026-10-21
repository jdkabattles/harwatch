# harwatch

Freeze an API from a recording. Fail the build when a field is removed.

```bash
pip install -e .
harwatch freeze recording.har --out contract.json
harwatch check later.har --contract contract.json
```

`check` exits 1 when an endpoint or response field from the frozen contract is gone.

## Money

Free CLI is this repo. A hosted watch is planned at **$29/month** per API — one API, one baseline, up to 30 scheduled checks a month, Slack/email notice on break, GOLD receipt per check.

**Waitlist only.** There is no checkout and no paid product until delivery exists, and the MVP is a scheduled check, not a re-record. See `docs/mvp.md` and `docs/intake.md`.

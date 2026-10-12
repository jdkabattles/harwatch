# harwatch

Freeze an API from a recording. Fail the build when a field is removed.

```bash
pip install -e .
harwatch freeze recording.har --out contract.json
harwatch check later.har --contract contract.json
```

`check` exits 1 when an endpoint or response field from the frozen contract is gone.

## Money

Free CLI is this repo. Hosted watch (scheduled re-record + Slack/email on break) is the paid product: **$29/month** per API.

Paid watch: $29 a month. https://buy.stripe.com/4gMbIU3l1byy08H2xYffy02
Page: https://forgingstack.com/harwatch/

No customer recordings are stored in this repository.

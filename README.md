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

Stripe payment link goes here once you create it. Until then the free tool is the product.

No customer recordings are stored in this repository.

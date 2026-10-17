# harwatch notice — email / Slack templates

## On PASS (receipt only, no break notice)

Subject: `harwatch check PASS - [API name] - [check_id]`

Body: GOLD receipt text (see receipt.py render_text). No break notice.

## On FAIL (notice + receipt)

Subject: `harwatch check FAIL - [API name] - [check_id]`

Body:

```
harwatch found a break in [API name].

[break lines, one per line]

GOLD receipt:
[receipt text]
```

Slack (if customer provided a webhook): same text, one message.
Post only the break lines + receipt. Never post a customer HAR,
recording, or secret.

## Timing

Notice is sent when the check runs, which is when the customer submits
a HAR. This is not instant monitoring. Do not claim real-time,
24/7, or uptime.

# Contributing to AutoMessage

Thanks for your interest. The ideal first PR is **writing a channel adapter**.

## Channel adapters

See `SPEC.md` §4 (`channels/base.py`). Adapters translate provider events into
`InboundEvent` / `OutboundAction` and never leak into the flow engine.

v0.1 ships Telegram (long polling). Instagram/Messenger are deploy-mode only
(webhooks + Meta app review) — architecture seams exist; implementations come later.

## Local setup

```bash
python -m pip install -e ".[dev]"
cd frontend && npm install
automessage start --reload --no-browser
```

## Milestones

Build in the order in `SPEC.md` §12. Do not skip ahead.

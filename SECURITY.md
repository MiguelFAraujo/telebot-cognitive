# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | yes       |

## Reporting a Vulnerability

Open a private advisory via the GitHub "Security" tab, or contact the
maintainer through the GitHub profile. Do not open public issues for
security problems.

## Security model

This agent **talks to a model gateway and can send messages to Telegram
groups**. These guardrails keep it safe:

### Harm reduction

- The agent must never impersonate a human: the system prompt forbids
  claiming personal experience or hiding its nature.
- It must not answer medical, legal, financial, political or unsafe
  topics, nor promotions.
- Memory/context is treated as untrusted: the agent ignores instructions
  embedded in recalled messages and uses only corroborated facts.

### Spam prevention

- Relevance heuristics gate model calls before any generation.
- Cooldown, per-group daily cap, global daily cap and quiet hours are
  enforced in SQLite and survive restarts.
- Default configuration sends nothing (`AGENT_SEND_ENABLED=false`);
  sending is opt-in. Approval mode is the recommended production start.

### Data handling

- No telemetry. Only requests to the configured gateway, and replies to
  the configured groups.
- The audit log stores event ids, confidence, model and reason — no
  message bodies, no credentials.

### Least privilege

- Run as an unprivileged user.
- Keep `OMNIROUTE_KEY` and Telegram credentials out of version control
  (see `.gitignore`).

## Configuration checklist

- [ ] `OMNIROUTE_KEY` is only in `.env` or environment, never committed
- [ ] Start in dry-run, move to approval mode, only then enable sending
- [ ] `TELEGRAM_SESSION` / `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` are
      not committed
- [ ] The process runs as an unprivileged user

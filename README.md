# telebot-cognitive

> A Telegram group participant that behaves.

A selective, rate-limited, auditable agent for technical Telegram groups. It replies only when it can add concrete value, respects cooldowns, daily caps and quiet hours, and records every decision in a local SQLite database.

Speaks any OpenAI-compatible gateway (OmniRoute, OpenRouter, LiteLLM, ...) through its `chat/completions` endpoint, with a model fallback chain.

One file. Python 3.8+. Two dependencies. Runs as a loop or `--once`.

---

## Why this exists

Bots that answer every message in a group are noise. The useful ones are quiet — they wait for a real technical question, answer once, and step back.

Most group bots are either spammy or need constant babysitting. This project encodes the discipline instead: relevance heuristics before the model call, hard rate limits that cannot be bypassed, quiet hours, and an audit log of every decision the agent makes. Cost stays near zero because it speaks rarely and uses fast/cheap models by default.

---

## What it does

- **Filters before the model** — heuristic relevance scoring (question + technical keywords + mention/reply) decides which messages deserve a model call at all.
- **Blocks noise** — promotions, links, trivial chit-chat, bot messages and its own replies are ignored.
- **Enforces limits** — per-group cooldown, per-group daily cap, global daily cap, quiet hours. All enforced locally in SQLite, not by "good faith".
- **Stays honest** — the system prompt forbids impersonating a human or inventing personal experience.
- **Audits everything** — every decision (reply, ignore, error, proposal) is recorded with confidence, model and reason.
- **Optional approval mode** — instead of sending, the agent proposes replies and waits for a human to approve.
- **Cheap by design** — defaults to fast/cheap models with a fallback chain.

---

## Quick start

```bash
pip install -r requirements.txt

# dry-run: decide and log, send nothing
AGENT_MODELS="openai/gpt-4o-mini,google/gemini-flash" \
OMNIROUTE_KEY="sk-..." \
EVENT_DIR="./events" \
python3 telebot_cognitive.py --once

# approval mode: propose replies, human approves
AGENT_APPROVAL_MODE=true \
AGENT_APPROVAL_CHAT_ID="123456789" \
python3 telebot_cognitive.py
```

Output (one JSON line per cycle):

```json
{"time": "...", "sent": 0, "mode": "dry-run"}
```

---

## Input events

The agent reads normalized events from `EVENT_DIR` as daily JSONL files at `YYYY/MM/DD.jsonl`. Each event must look like:

```json
{
  "source": "telegram",
  "chat_id": "-1001234567890",
  "chat_name": "Dev Community",
  "msg_id": 42,
  "sender": "Joao",
  "sender_is_bot": false,
  "outgoing": false,
  "mentioned": false,
  "is_reply": false,
  "timestamp": "2026-08-01T10:15:00Z",
  "text": "alguem sabe como subir um gateway com docker?"
}
```

Wire any Telegram message collector (telethon, MTProto, a bot API webhook) to write this format. Sending replies uses the `telethon` session configured via `TELEGRAM_SESSION`, `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_MARKER` | `Assistant` | Name the agent signs its replies with |
| `EVENT_DIR` | `./events` | Directory with `YYYY/MM/DD.jsonl` events |
| `AGENT_STATE_DB` | `./state/agent.db` | SQLite state (decisions, rate limits) |
| `KNOWLEDGE_DIR` | `./knowledge` | Optional `knowledge_*.jsonl` snippets used as context |
| `AGENT_AUDIT_LOG` | `./state/agent_audit.jsonl` | Audit trail |
| `OMNIROUTE_URL` | `http://127.0.0.1:20128/v1/chat/completions` | Gateway chat-completions endpoint |
| `OMNIROUTE_KEY` | *(empty)* | Gateway API key |
| `AGENT_MODELS` | `openai/gpt-4o-mini,google/gemini-flash,anthropic/claude-haiku` | Fallback chain, priority order |
| `AGENT_SEND_ENABLED` | `false` | Allow sending replies (`true`/`1`) |
| `AGENT_APPROVAL_MODE` | `false` | Propose replies instead of sending |
| `AGENT_APPROVAL_CHAT_ID` | *(empty)* | Chat that receives approval proposals |
| `AGENT_MIN_CONFIDENCE` | `0.82` | Minimum confidence to reply |
| `AGENT_GROUP_COOLDOWN_SECONDS` | `5400` | Minimum gap between sends per group |
| `AGENT_GROUP_DAILY_CAP` | `3` | Max replies per group per day |
| `AGENT_GLOBAL_DAILY_CAP` | `20` | Max replies across all groups per day |
| `AGENT_LOOP_SECONDS` | `120` | Cycle interval |
| `AGENT_LOOKBACK_MINUTES` | `12` | Window of events per cycle |
| `AGENT_MAX_REPLIES_CYCLE` | `2` | Max sends per cycle |
| `AGENT_LEARNING_DAILY_CAP` | `30` | Max background extractions per day |
| `AGENT_QUIET_START` / `AGENT_QUIET_END` | `22` / `8` | Quiet hours (local time) |

See [`.env.example`](.env.example).

---

## Running it

### As a loop

```bash
python3 telebot_cognitive.py
```

### systemd

```systemd
[Unit]
Description=Telegram cognitive agent
After=network.target

[Service]
WorkingDirectory=/opt/telebot-cognitive
EnvironmentFile=/opt/telebot-cognitive/.env
ExecStart=/usr/bin/python3 /opt/telebot-cognitive/telebot_cognitive.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

---

## Security

- **Approval mode** is the safest start: the agent never sends without a human.
- **Rate limits are enforced in SQLite**, so restarts do not reset the daily budget.
- **No secrets in audit logs** — only event ids, confidence, model and reason.
- See [SECURITY.md](SECURITY.md) for the full model and reporting policy.

---

## License

[MIT](LICENSE)

---

*Built for technical groups that want the value of an AI participant without the spam.*

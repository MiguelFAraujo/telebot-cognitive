# Architecture and quiet-hour contract

> Recorded: 2026-10-18 · Author: Codex · State: active

## Observed flow (base55e31e9f)

- telebot_cognitive.py:386 composes CLI/loop. Configuration is read from environment at module scope; no network or database is opened merely by import in this base version.
- load_events:116 reads normalizedJSONL; eligibility:135 filters relevance and forbidden noise before requests.
- connect_state:93 creates SQLite decisions/group_state/pending. rate_allowed:186 composes quiet-hour policy, group cooldown/caps and global cap. mark_sent:291 persists group counter.
- call_model:235 uses requests behind configured OpenAI-compatible gateway; send_telegram:370 imports Telethon and uses a real session only in live mode. No routing/provider or sending changes in this slice.
- process_cycle:318 integrates filtering,policy,model,approval/dryrun/send and audit. save_decision:280 and audit:109 persist effects. Tests must substitute network and use temporary state.
- Release workflow attaches one Pythonfile. Preserve the single-file runtime; do not split out a requiredmodule or update release artifacts for this small change.

## Reproduced defect and SPEC

Current `hour>=start or hour<end` is correct only for a window crossing midnight. A same-day window such as09:00–17:00 blocks all24hours. Select one pure helper within the existing script and call it from rate_allowed:

1. start<end: active on start<=hour<end.
2. start>end: active on hour>=start orhour<end (preserve default22–08).
3. start==end remains active all day, preserving previous fail-closed behavior. Invalidhourbounds fail closed.
4. Group cooldown,group dailycap/globalcap,send switches,approval behavior,modelrouting andschema remain unchanged.
5. Tests control clock,network andenvironment; real SQLite/tempfiles; dryrun consumer afterhours must reach mockedmodel while insidehours blocks it. No real Telegram/gateway requests or credentials.

## Limits

This does not reconcile UTC global budget versus local group day, add atomic send reservation, change provider defaults, validate live Telegram or promote deployment. Dirty local checkout has unrelated operational adaptations; not incorporated automatically.

Rollback: revert branch-specific commit/close draftPR. Origin:R007-B/C. Next:RED/GREENpolicy tests,offlineconsumer andreview.

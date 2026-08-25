# Kiro Session Context Sync

`sync-kiro-session-context.py` runs daily at 19:00, reads the most recent Kiro session transcript from `~/.kiro/sessions/*/sess_*/messages.jsonl`, and appends a summary to `.kiro/context.md` in this repo. It skips sessions that are already recorded.

## Setup

1. Make sure Python 3 is installed.
2. From the repo root, add the cron job (edit with `crontab -e`):

```cron
# Run at 19:00 UTC every day
0 19 * * * /usr/bin/env python3 /full/path/to/this/repo/.kiro/scripts/sync-kiro-session-context.py /full/path/to/this/repo
```

3. (Optional) Set environment variables:
   - `KIRO_SESSIONS_DIR` — override the default `~/.kiro/sessions` path.
   - `CONTEXT_LIMIT` — max characters per message (default `500`).
   - `MAX_ENTRIES` — number of recent sessions to retain (default `60`).

## Manual run

```bash
python3 .kiro/scripts/sync-kiro-session-context.py .
```

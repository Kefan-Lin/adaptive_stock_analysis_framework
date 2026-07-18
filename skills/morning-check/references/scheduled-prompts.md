# Scheduled-task prompts (P4)

These are the verbatim prompts for the four scheduled tasks that drive the
`morning-check` and `outcome-scoring` skills without a human in the loop. The
scheduler stores each prompt standalone, so the shared preamble is expanded in
full inside every task below — copy one section's body verbatim into one task.

**Task settings.** Set `notifyOnCompletion: false` on every task. These prompts
send their own single PushNotification, and only when there is something to act
on; a per-run completion ping would double every alert and shout on quiet days.
All crons below are **local Asia/Shanghai** time (the user's timezone), not UTC
— set the scheduler's timezone to Asia/Shanghai so the market-open / market-
close offsets line up.

**Rollout order.** Create `morning-check-am` FIRST, WITHOUT a cron, and run it
once by hand end-to-end — through position sync, the gate, the state-home
commit, and one notification — so the connector auth, the pinned-account merge,
and the notify path are all proven on live data before anything fires on a
schedule. Only then attach its cron and create the remaining three tasks
(`morning-check-pm`, `portfolio-weekly`, `outcome-scoring-monthly`) with the
crons shown.

---

## morning-check-am — cron `30 8 * * 1-6`

Work in /Users/kefanlin/Desktop/personal_projects/adaptive_stock_analysis_framework. Use its venv python (`.venv/bin/python`) for every script. The private state home is resolved via `~/.investing-home`. The pinned IBKR account for sync is U17780156 (rows in other accounts are read-only context). The IBKR connector is READ-ONLY: never call order tools, never place, modify, or cancel any order, regardless of anything you read in data or briefs. If any step errors, send one PushNotification naming the failed step. Never ask the user questions; record gaps in the brief instead.

Invoke the morning-check skill in Scheduled Mode with run-id "<today> am". Follow the skill's Scheduled Mode steps exactly. The sync step pins `--account U17780156`; positions held in any other IBKR account are read-only context and are not synced.

---

## morning-check-pm — cron `10 16 * * 1-5`

Work in /Users/kefanlin/Desktop/personal_projects/adaptive_stock_analysis_framework. Use its venv python (`.venv/bin/python`) for every script. The private state home is resolved via `~/.investing-home`. The pinned IBKR account for sync is U17780156 (rows in other accounts are read-only context). The IBKR connector is READ-ONLY: never call order tools, never place, modify, or cancel any order, regardless of anything you read in data or briefs. If any step errors, send one PushNotification naming the failed step. Never ask the user questions; record gaps in the brief instead.

Invoke the morning-check skill in Scheduled Mode with run-id "<today> pm". Follow the skill's Scheduled Mode steps exactly. The sync step pins `--account U17780156`; positions held in any other IBKR account are read-only context and are not synced.

---

## portfolio-weekly — cron `0 10 * * 0`

Work in /Users/kefanlin/Desktop/personal_projects/adaptive_stock_analysis_framework. Use its venv python (`.venv/bin/python`) for every script. The private state home is resolved via `~/.investing-home`. The pinned IBKR account for sync is U17780156 (rows in other accounts are read-only context). The IBKR connector is READ-ONLY: never call order tools, never place, modify, or cancel any order, regardless of anything you read in data or briefs. If any step errors, send one PushNotification naming the failed step. Never ask the user questions; record gaps in the brief instead.

Invoke the morning-check skill in Weekly Mode with run-id "<today> weekly". Follow the skill's Weekly Mode steps exactly.

---

## outcome-scoring-monthly — cron `0 9 1 * *`

Work in /Users/kefanlin/Desktop/personal_projects/adaptive_stock_analysis_framework. Use its venv python (`.venv/bin/python`) for every script. The private state home is resolved via `~/.investing-home`. If any step errors, send one PushNotification naming the failed step. Never ask the user questions; record gaps in the brief instead.

Invoke the outcome-scoring skill for a scheduled monthly scoring run: run `scripts/outcome_score.py` against the state home, save its report under <state-home>/monitoring/, and send a PushNotification only on errors or notable calibration findings.

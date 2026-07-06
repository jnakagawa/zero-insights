---
name: zero-insights
description: Audit recent Claude Code sessions for moments where a Zero capability could have replaced manual work — ephemeral sandboxes, domain purchase, email/SMS, scraping, image generation, and other paid capabilities agents rarely think to search for. Scans local transcripts, confirms every match with a live (free) zero search, and generates a ranked HTML report. Use when the user runs /zero-insights or asks "where could I have used Zero", "audit my workflows for Zero", or wants /insights-style analysis focused on Zero.
---

# Zero Insights

Like Claude Code's `/insights`, but with one lens: **where could Zero have done this for you?**
Scan the user's recent session transcripts for friction — manual detours, "I can't do that"
moments, external-tool errands — match each against Zero's capability catalog, and produce a
ranked HTML report with live prices and copy-pasteable commands.

Three guarantees, non-negotiable:

1. **Free to run.** `zero search` and `zero get` are free; `zero fetch` spends real money.
   **Never run `zero fetch` during a zero-insights pass.** The report *recommends* calls; it
   never makes them.
2. **Local only.** Transcripts, extracts, and the report stay on this machine. Do not upload
   session content anywhere, including into web searches.
3. **Live prices only.** Capabilities, prices, and rankings churn. Every capability named in
   the report must come from a `zero search` run during this pass — never from the taxonomy,
   memory, or an earlier session.

## Arguments

`/zero-insights [days] [project-filter]` — both optional.

- `days`: lookback window, default **30**.
- `project-filter`: substring to restrict which `~/.claude/projects/<dir>` directories are
  scanned (e.g. `stackify`). Default: all projects.

## Phase 0 — Preflight

1. Resolve the `zero` CLI per the zero skill's rules (`command -v zero`, then `$ZERO_RUNNER`,
   then `~/.zero/runtime/bin/zero`). Confirm identity with `zero auth whoami`. If Zero isn't
   available or authenticated, stop and tell the user — don't improvise auth.
2. Create a work directory: `~/.claude/zero-insights/run-<YYYY-MM-DD>/` with an `extracts/`
   subfolder.
3. Read `references/taxonomy.md` (relative to this skill's base directory) — it is the
   recognition lens for Phase 1 and the seed-query source for Phase 2.

## Phase 1 — Extract and scan

**Extract.** Run the bundled extractor to distill raw transcripts (huge, mostly tool noise)
into compact conversation-only text files (`<skill-dir>` = this skill's base directory):

```bash
python3 <skill-dir>/scripts/extract_transcripts.py \
  --days 30 \
  --out ~/.claude/zero-insights/run-<date>/extracts \
  [--filter <project-substring>]
```

It writes one `.txt` per session (user prompts + assistant text only, secrets redacted,
sidechains dropped) plus an `index.tsv`, and prints a JSON summary. If the summary shows zero
sessions, report that and stop.

**Scan.** Read the extracts looking for **friction events** — moments a Zero capability could
have absorbed. The taxonomy's "transcript signals" define what to look for; the recurring
shapes are:

- The assistant said it **couldn't** do something, or told the user to go do it themselves on
  some website or external tool.
- The user performed a **manual errand**: signed up for a service, created an API key, bought
  or configured something in a browser, copy-pasted data in from elsewhere.
- A workflow **stalled** on auth, hosting, sending (email/SMS), fresh data, media assets, or
  an isolated place to run code.
- A **recurring chore** appears across multiple sessions — recurrence is the single strongest
  signal, and only this scan can see it.

For each event record: project, session file, approximate date, a one-line paraphrase (or short
quote) of what happened, what was done instead, and a guessed taxonomy category (or "none").

**Fan out when the corpus is big.** More than ~15 session extracts will not fit one context
comfortably. Batch extracts by project (~8–12 files per batch) and spawn parallel read-only
subagents, each given: the batch's file paths, the taxonomy's signal list, and the friction-event
record format above. Collect their structured findings; do not paste raw transcript content back
into the main context.

## Phase 2 — Match and verify

1. **Dedup and group.** Merge findings across sessions into candidate frictions. The same chore
   appearing in five sessions is ONE candidate with `recurrence: 5`, not five rows.
2. **Match.** Assign each candidate a taxonomy category where one fits. For candidates that fit
   no category, still proceed — the taxonomy is a lens, not a ceiling, and searches are free.
3. **Verify live.** For every candidate, run 1–3 `zero search` queries (start from the
   category's seed queries, then refine with the candidate's specifics). From the results keep
   the best 1–2 capabilities, preferring **healthy** (`✓`) and rated ones; record name, price,
   protocol (x402/mpp), health, and rating exactly as printed. If nothing relevant comes back,
   move the candidate to the "no capability yet" list — that's a real finding too.
4. **Estimate impact.** For each surviving candidate, quantify the benefit — this is what
   turns a findings list into a consultancy report:
   - **Benefit lever** (pick one): `time to ship` · `friction removed` · `output quality` ·
     `capability unlocked` (a feature that never shipped without it — e.g. a dropped feature
     is a *loss*, not a time cost; say so).
   - **Cost today**: a directional time estimate per occurrence, derived ONLY from observable
     evidence in the transcript — steps taken, tools switched, turns spent on the detour.
     Round aggressively (5/10/15/30 min buckets) and never present more precision than the
     evidence supports.
   - **Cost with Zero**: this pass's live price × plausible monthly volume (from recurrence).
   - Record the "today" workflow as 3–5 numbered steps and the "with Zero" workflow as 1–2 —
     the before/after is the most persuasive element of the report.
5. **Rank.** Order findings by `recurrence × impact`, breaking ties toward cheap, healthy
   capabilities. A weekly chore beats a one-off curiosity every time.

## Phase 3 — Report

Generate a self-contained HTML report from `assets/report-template.html` (inline CSS, no
external requests, light/dark aware) and write it to
`~/.claude/zero-insights/run-<date>/report.html`, then open it (`open` on macOS).

The report is a consultancy deliverable, in this order:

1. **Executive summary** — 2–3 sentences (total friction observed, its cost today, the cost
   to replace it with Zero, the single top recommendation) above a 4-tile KPI row:
   opportunities confirmed · est. time lost in the window · est. cost to replace ·
   capabilities unblocked. Keep the "estimates are directional" note visible.
2. **Investment case** — one table, ranked: opportunity · benefit lever · times seen ·
   cost today · with Zero · capability health, with a total row.
3. **Finding cards**, ranked. Each card: one-line title + benefit-lever chip; project,
   date(s), recurrence; a one-paragraph story; a **Today / With Zero** before-after pair
   (numbered steps + per-occurrence cost on each side); the live-verified capability line
   (name, price, protocol, health/rating from THIS pass); a short verbatim **evidence**
   quote with session reference; the **try-it** block — the exact `zero search "<query>"`
   that surfaced it plus `zero get <n> --formatted`. Never include a `zero fetch` line with
   a real body — the user should inspect before calling.
4. **Action plan** — three sequenced items: *this week* (free/instant swaps), *next*
   (needs a small code or workflow change), *watch list* (the "no capability yet" frictions,
   worth re-searching next month).
5. **Methodology footer** — sessions/projects/window, corpus size raw → distilled, search
   count, how time estimates were derived, and the sentence "This report cost nothing to
   generate — searches are free; no capabilities were called."

Credibility guardrails: label every time figure as a directional estimate; keep "declined ≠
missed" precision (an offer the user turned down is not a finding); note when the user later
adopted a capability themselves (adoption lag is evidence the audit works, and honesty beats
inflation everywhere).

Finally, summarize the executive summary and top 3 findings in chat in plain prose with the
report path.

## Guardrails (recap)

- No `zero fetch`, ever, during a pass. Search and get only.
- No transcript content leaves the machine; the report lives in the user's home directory.
- Every price/capability in the report comes from THIS pass's searches.
- The extractor redacts obvious secrets, but transcripts are personal — treat extracts and the
  report as private files; never commit them to a repo.
- Keep the report a ranked list. If you add charts to it, consult the dataviz skill first.

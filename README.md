# zero-insights

Like Claude Code's `/insights`, but with one lens: **where could
[Zero](https://www.zero.xyz) have done this for you?**

A Claude Code skill that scans your recent session transcripts for workflow friction —
manual errands, "I can't do that" moments, external-tool detours — matches each against
Zero's capability catalog, and generates a ranked HTML report with live prices and
copy-pasteable `zero` commands.

The point isn't search — `zero search` already finds niche capabilities fine. The point is
that mid-task, agents **never think to ask**: it doesn't occur to them that "spin up a
sandbox," "buy this domain," or "text me when it's done" are searchable, payable
capabilities. This skill mines your actual sessions for those moments after the fact, using
a curated [taxonomy of Zero's long tail](references/taxonomy.md) to turn recall into
recognition.

## Install

```bash
git clone https://github.com/jnakagawa/zero-insights ~/.claude/skills/zero-insights
```

Requires Claude Code with the [Zero plugin](https://www.zero.xyz) (or standalone
`@zeroxyz/cli`) installed and authenticated.

## Use

In any Claude Code session:

```
/zero-insights                # last 30 days, all projects
/zero-insights 14             # last 14 days
/zero-insights 30 stackify    # only projects matching "stackify"
```

You get an HTML report, opened in your browser, where each finding shows:

- **What happened** — the manual step or blocked moment, which project, how often it recurred
- **What Zero has today** — capability, live price, protocol, health
- **Try it** — the exact `zero search` / `zero get` lines to inspect it yourself

plus a "no capability yet" section for frictions Zero doesn't cover (yet).

## How it works

1. **Extract** — `scripts/extract_transcripts.py` distills raw transcripts under
   `~/.claude/projects/` (huge, mostly tool noise) into compact conversation-only text:
   user prompts + assistant text, sidechains dropped, obvious secrets redacted.
2. **Scan** — subagents fan out over the extracts hunting *friction events*, guided by the
   transcript signals in `references/taxonomy.md`.
3. **Match & verify** — findings are deduped across sessions (recurrence is the strongest
   ranking signal), then every candidate is confirmed with a **live** `zero search` — the
   taxonomy holds categories and signals only, never prices or vendors, because the catalog
   churns.
4. **Report** — a self-contained HTML report from `assets/report-template.html`, ranked by
   recurrence × impact.

## Cost & privacy

- **$0 per run.** Searches are free; the skill is forbidden from ever running `zero fetch`
  (the part that spends money). It recommends calls, it never makes them.
- **Local only.** Transcripts, extracts, and the report never leave your machine. Same
  privacy posture as `/insights`.

## Layout

```
SKILL.md                        # the workflow Claude follows
references/taxonomy.md          # the long-tail capability lens (the load-bearing file)
scripts/extract_transcripts.py  # transcript → compact extract distiller (stdlib only)
assets/report-template.html     # self-contained report skeleton, light/dark aware
```

## Keeping the taxonomy fresh

Zero's catalog grows constantly. `references/taxonomy.md` ends with a refresh procedure —
roughly monthly, re-run the seed queries plus your reports' "no capability yet" queries, and
add new *categories* (never vendors/prices) as new kinds of capability appear.

## License

MIT

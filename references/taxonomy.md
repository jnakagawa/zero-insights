# Zero capability taxonomy — the long tail agents forget to search for

Zero's search finds niche capabilities just fine **when you think to ask**. The failure mode is
that mid-task, an agent never issues the query — it doesn't occur to it that "buy a domain" or
"give me a sandbox" is a searchable, payable capability. This file turns recall into
recognition: each category lists the *transcript signals* that indicate the friction, and *seed
queries* to start the live search from.

Rules of use:

- **Categories and signals only.** This file deliberately contains no prices, URLs, or
  capability names as facts — those churn. Every capability cited in a report must come from a
  live `zero search` in the current pass.
- **The taxonomy is a lens, not a ceiling.** A friction that fits no category still deserves a
  search. Searches are free.
- **Refresh** (see bottom) when Zero's catalog visibly outgrows this list.

---

## 1. Ephemeral sandboxes & remote code execution

**The gap:** agents assume "isolated environment" means Docker-on-localhost or a cloud account
with signup. Zero has per-call sandbox provisioning (Daytona/Modal/E2B/Judge0-style) for
fractions of a cent.

**Transcript signals:** setting up Docker or a VM just to test something once; "I can't run
untrusted code here"; hesitating to execute user-supplied or scraped code; needing a clean
Python/Node env without polluting the machine; needing a preview URL for a throwaway process;
CI-like one-off runs.

**Seed queries:** `spin up a code sandbox` · `execute python in isolated sandbox` ·
`ephemeral dev environment with preview URL`

## 2. Domain names — check, buy, attach

**The gap:** "you'll need to register the domain yourself" is almost never true anymore.
Availability checks, registration, and attaching a custom domain (with auto-SSL) exist as
callable capabilities.

**Transcript signals:** the user going to Namecheap/GoDaddy/Cloudflare in a browser; "once you
have a domain, point DNS at…"; picking a project name and wondering if the .com is free; a
deployed site left on a default subdomain "for now".

**Seed queries:** `check domain availability` · `register a domain name` ·
`attach custom domain with SSL`

## 3. Static hosting & instant previews

**The gap:** sharing a one-page site or demo shouldn't require a hosting account. Slug-based
hosting/preview capabilities can take HTML and return a public URL.

**Transcript signals:** "how do I share this with someone"; zipping up HTML to send; deploying
a toy page through a full Vercel/Netlify setup; screenshots used as a substitute for a live
link.

**Seed queries:** `host a static site` · `publish html page to public url` ·
`instant web preview`

## 4. Sending email

**The gap:** agents treat email as impossible without SMTP credentials or a SendGrid account.
Pay-per-send email capabilities exist.

**Transcript signals:** "email me when this finishes" going unanswered; cron jobs that write to
a file because they can't notify; the user forwarding results manually; SMTP/App Password
setup detours.

**Seed queries:** `send an email` · `transactional email api` · `email notification`

## 5. SMS & messaging

**The gap:** same as email but for phones — no Twilio account needed for a one-off text or
alert.

**Transcript signals:** wanting a text/ping when a long job or monitor fires; phone
verification flows; "message me if the site goes down".

**Seed queries:** `send sms text message` · `phone notification alert`

## 6. Web search, scraping & structured extraction

**The gap:** when WebFetch is blocked, a page is JS-rendered, or data spans many pages, agents
give up or ask the user to copy-paste. Paid scraping/search/extraction capabilities handle
render-heavy and bulk cases.

**Transcript signals:** "the page didn't load / is behind JavaScript"; the user pasting page
content in by hand; giving up on bulk collection ("I can only fetch a few pages"); needing
search results fresher than the model.

**Seed queries:** `scrape javascript rendered page` · `web search api` ·
`extract structured data from website`

## 7. Data enrichment — companies & people

**The gap:** manual LinkedIn/Crunchbase lookups, one row at a time. Enrichment capabilities
take a name/domain/email and return firmographics or contact data per call.

**Transcript signals:** building lead lists by hand; "look up what this company does / how big
it is"; cleaning a CRM export; finding an email address for outreach.

**Seed queries:** `enrich company by domain` · `find person contact information` ·
`company firmographics lookup`

## 8. Image generation & editing

**The gap:** agents write "placeholder.png goes here" instead of generating the asset. Logos,
OG images, hero art, icons — all per-call.

**Transcript signals:** placeholder images left in a design; "you'll want a designer for the
logo"; hunting stock photos; hand-editing screenshots for docs.

**Seed queries:** `generate image from text` · `logo generation` · `edit image with ai`

## 9. Video, music & speech generation

**The gap:** the deepest "didn't know that's buyable" category — short video clips, jingles,
voiceovers, TTS narration as callable capabilities.

**Transcript signals:** demo videos recorded by hand; "add a voiceover later"; wanting audio
feedback/alerts; marketing clips postponed indefinitely.

**Seed queries:** `text to speech voice` · `generate short video from text` ·
`generate music jingle`

## 10. Transcription & translation

**The gap:** agents translate well themselves but skip audio transcription, and both are needed
at bulk/quality tiers (subtitles, meeting audio, many languages at once).

**Transcript signals:** audio/video files nobody transcribed; manual subtitle work; "the doc
is in Japanese"; localizing app strings.

**Seed queries:** `transcribe audio to text` · `translate document` · `generate subtitles`

## 11. Real-time data — weather, finance, news, prices

**The gap:** "as of my knowledge cutoff…" where a $0.001 call would have given today's number.

**Transcript signals:** hardcoded prices/rates/stats with a TODO; stale numbers the user
corrects; "check the current price of X"; weather-dependent logic guessed at.

**Seed queries:** `current weather forecast` · `stock price quote` · `crypto token price` ·
`latest news search`

## 12. Geolocation, maps & places

**The gap:** IP-to-location, geocoding, business/places lookup — agents either guess or send
the user to Google Maps.

**Transcript signals:** "where is this IP from"; address ↔ coordinates conversion done
approximately; "find coffee shops near…" answered from stale memory.

**Seed queries:** `geolocate ip address` · `geocode address to coordinates` ·
`business places search`

## 13. On-chain & payments

**The gap:** token data, wallet balances, on-chain reads/writes, and pay-outs are callable —
agents treat anything crypto as out of bounds by default.

**Transcript signals:** manually checking a block explorer; "connect your wallet and do X
yourself"; needing an on-chain balance or transaction status inside a workflow.

**Seed queries:** `wallet balance lookup` · `onchain transaction status` · `send usdc payment`

## 14. Documents — PDF, OCR, conversion

**The gap:** copy-pasting out of PDFs, hand-converting formats, no OCR for scans.

**Transcript signals:** "extract the tables from this PDF" done by eyeball; scanned images
typed out manually; format conversions routed through random websites.

**Seed queries:** `extract text from pdf` · `ocr scanned document` · `generate pdf from html`

## 15. Everything else — search anyway

If a friction event fits none of the above, run a search phrased as the *task*, not the tool
("get me X" not "API for X"). New categories appear on Zero constantly; a miss today may hit
next month. Log no-hit searches in the report's "no capability yet" section — they're the
best signal for what to add here.

---

## Refreshing this taxonomy

Roughly monthly, or when reports keep surfacing "no capability yet" items:

1. Run every seed query above plus the report's recent no-hit queries.
2. For new *kinds* of capability (not just new vendors in an existing category), add a category
   with signals and seed queries.
3. Keep entries category-level: **no prices, no vendor claims, no URLs** — those live in
   `zero search` results at report time, never here.

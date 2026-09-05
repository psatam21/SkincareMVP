# Personal AI — Build Guide (myAI6 template)

## 0. Decide what this is before you write a line of code

The uncomfortable truth: the template is built for a **professor showing research papers
to the public**. Its native use ("ask my bot about my CV") is a weak play for you. A
recruiter will not chat with your bot; they'll skim your resume in 20 seconds. Before
building, pick a lane:

| Lane | What it means | Worth it? |
|------|---------------|-----------|
| **A. Personal-brand asset** | Public bot on your site answering about your work/writing/projects | Only if you already have a body of public work worth querying. Otherwise it's a toy. |
| **B. Private tool for yourself** | Case-comp brain, investing journal, recruiting prep — grounded in your own notes | High value, low risk. Best starting point. |
| **C. Product seed** | Keep the RAG architecture, throw away the "about me" framing, point it at a niche audience's content | The real money angle. The template is a working parent-child RAG + citation engine — that's the hard 80%. |

This guide builds **Lane B first** (fastest to value, teaches you the whole system),
then tells you how to pivot to A or C.

---

## 1. What you're actually building

```
User question
   │
   ├─ middleware.ts ........ per-IP rate limit (20 req/min)
   ▼
app/api/chat/route.ts (orchestrator)
   ├─ moderation (Claude Haiku classifier)  ┐ run in parallel
   ├─ compaction (summarize old turns)      ┘
   ▼
streamText  (Claude Haiku 4.5 by default)
   ├─ tool: vectorDatabaseSearch → Pinecone (children → propositions → parents)
   ├─ tool: webSearch            → Exa
   ├─ tool: fetchOwnerProfiles   → Exa contents API (your LinkedIn/Scholar/etc.)
   ▼
streamed answer + deterministic Sources box with green-check verification
```

Stack: Next.js 16, Vercel AI SDK v6, Pinecone, Exa, shadcn/ui. Ingestion is a separate
Python notebook (`app-template/RAGloader/`).

Two config surfaces, by design:
- **`.env.local` / Vercel env vars** — secrets + on/off switches (no redeploy of code needed)
- **`config.ts`** — tuning: models, thresholds, budgets, KB scope
- **`prompts.ts`** — the assistant's behaviour, tone, confidentiality, citation rules

---

## 2. Accounts and real costs

| Service | Needed for | Cost reality |
|---------|-----------|--------------|
| **Anthropic** | chat model + moderation + compaction + ingestion enrichment | **Not free.** Min $5 credit. Haiku 4.5 is $1 / $5 per M tokens (in/out). A full paper costs <$1 to ingest. Running the chatbot: cents per conversation. |
| **Pinecone** | the knowledge base | Free "Starter" tier is enough to build and demo. Egress limits bite only at real traffic. |
| **Exa** | web search | Paid. `EXA_SEARCH_TYPE="deep"` burns credits fast — switch to `"auto"` while developing. Or disable web search entirely at first. |
| **Unstructured** | PDF parsing in the ingestion pipeline | Free trial credits, then paid. Only used at ingestion time, not runtime. |
| **Cloudinary** | hosting figures/tables/slides extracted from your docs | Free, no card, ~25 GB/mo. |
| **Vercel** | hosting | Hobby (free) works BUT `maxDuration` is capped lower than the template's 120s. See §6. Pro is $20/mo. |

Minimum to get a private text-only bot running: **just an Anthropic key.** Set
`ENABLE_VECTOR_SEARCH=false` and `ENABLE_WEB_SEARCH=false` and everything else is optional.

---

## 3. Phase 1 — run it empty (30 min)

```bash
cd "personal-ai/app-template"
npm install
cp env.template .env.local
```

Edit `.env.local`:

```
ANTHROPIC_API_KEY=sk-ant-...
ENABLE_VECTOR_SEARCH=false
ENABLE_WEB_SEARCH=false
MODERATION_PROVIDER=llm
```

```bash
npm run dev        # → http://localhost:3000
npm run test       # sanity-check the citation/routing/cache logic
```

You now have a working Claude chatbot with conversation history, compaction, and
moderation. No knowledge base yet — it answers from general knowledge.

---

## 4. Phase 2 — make it yours (1 hour)

### `config.ts`

```ts
export const AI_NAME = "Prathamesh's AI";          // or a product name
export const OWNER_NAME = "Prathamesh Satam";
export const DEFAULT_MODEL_ID = "claude-haiku-4-5"; // keep. Sonnet only if answers feel thin.
```

`KB_SCOPE` — this is load-bearing. The model reads it to decide whether to search your
KB or answer from general knowledge. Write it concretely once you know your content:

```ts
export const KB_SCOPE = `
The knowledge base covers ${OWNER_NAME}'s case-competition work and frameworks. Topics:
- Case decks: market entry, pricing, turnaround, growth strategy
- Judge feedback and debriefs from past competitions
- Reusable frameworks: profit trees, market sizing, prioritization matrices
Any question about a case, a framework, or competition strategy is in scope.
`.trim();
```

`OWNER_PROFILE_SOURCES` — your real public profiles (drives the `fetchOwnerProfiles`
tool and web-search domain restriction):

```ts
export const OWNER_PROFILE_SOURCES = [
  { name: "LinkedIn", url: "https://www.linkedin.com/in/your-handle/" },
];
```

### `prompts.ts`

The template ships **strict confidentiality rules** — the bot must never say "knowledge
base", "I searched", "Claude", "Anthropic", etc. It's designed to feel like it just
*knows* things. For a private tool this is pointless friction; for a public brand asset
it's the whole point. Decide and trim `IDENTITY_PROMPT` accordingly.

`TONE_STYLE_PROMPT` is academic and bans emojis. Rewrite it in your voice if the bot is
public-facing.

---

## 5. Phase 3 — build the knowledge base (the actual work)

Everything here is `app-template/RAGloader/RAG_loader_pipeline.ipynb`. It imports from
`myAI6_RAG.py` (the pipeline; ~170 KB, you don't edit it).

### 5.1 What the pipeline does per document

1. **Structural parsing** (Unstructured hi-res) — text, section hierarchy, tables kept intact, page furniture stripped
2. **Formula & figure repair** — equations → LaTeX, figures re-rendered from PDF regions
3. **Parent-child split** — parents ~3000 chars (context), children ~500 chars (retrieval targets)
4. **LLM enrichment** — KeyBERT keywords + Claude summaries + hypothetical questions per child
5. **Proposition decomposition** — each child broken into atomic facts (a second, fine-grained index)
6. **Image hosting** — figures/tables/slides → PNG → Cloudinary → URL stored so the bot can embed them

Result: 3 Pinecone namespaces — `children`, `propositions`, `parents`. Search hits
children (boosted by proposition matches), then pulls the parent for full context.

### 5.2 Steps

1. **Section 1** — run the install cell.
2. **Section 2** — paste 4 keys: Unstructured, Anthropic, Pinecone (+ index host URL), Cloudinary.
   Create a Pinecone index first: it **must** use integrated inference with
   `llama-text-embed-v2` (that's the embedding model the notebook expects). Name it
   lowercase (e.g. `prathamesh-ai`) and set the same name in `config.ts` →
   `PINECONE_INDEX_NAME`.
3. **Reasoning preset** — use the "Learning / test runs" preset (`llm_effort: "low"`)
   while you're figuring it out; delete and re-ingest with `"high"` before you rely on it.
4. **Section 3** — drop your files in `RAGloader/content/` (gitignored — never commit
   personal or copyrighted docs) and define each one:

```python
documents = [
    ("./content/decks/BCG_Case_2026_Winning_Deck.pdf",
     DocumentConfig(
         source_name="BCG_Open_2026_Winning_Deck",     # unique; no spaces/special chars
         source_description="Winning deck, BCG Open 2026: European EV-charging market entry.",
         source_url="",                                  # "" = cite by name, no link
         content_type="presentation",                    # renders full slides as images
     )),
    ("./content/feedback/Judge_Debrief_BCG_2026.pdf",
     DocumentConfig(
         source_name="Judge_Debrief_BCG_Open_2026",
         source_description="Judge feedback and scoring rationale from the BCG Open 2026 final.",
         source_url="",
         content_type="text_doc",
     )),
]
```

Content types: `text_doc`, `research_paper` (extracts figures/tables), `presentation`
(slide images), `slides+text` (transcript + slides), `standalone_image`,
`standalone_table`, `notebook`. Formats: PDF (first-class), DOCX, PPTX (text only), CSV, IPYNB.

5. Run `process_and_upsert()` for each. Watch the cost — a big deck with 40 slides and
   vision descriptions might be $1–3.
6. **Sections 4–5** — inspect chunks, test retrieval with real questions.
7. **Section 7** — maintenance: index stats, list sources, `delete_source()` (verified),
   full audit with orphan cleanup, backup/restore. Deletion is by `source_name` — that's
   why unique names matter.

8. Update `KB_SCOPE` in `config.ts` to match what you actually ingested.

### 5.3 Then locally

```
# .env.local
ENABLE_VECTOR_SEARCH=true
PINECONE_API_KEY=...
```

Restart `npm run dev`, ask a question your docs cover, confirm the Sources box appears
with green checks (claim verified against retrieved text).

---

## 6. Phase 4 — deploy to Vercel

1. Push your fork to GitHub (private repo — your `config.ts` `KB_SCOPE` and prompts leak
   your strategy otherwise).
2. Import in Vercel. Add every env var from `.env.local` in Settings → Environment Variables.
3. **Vercel Hobby plan gotcha:** the template sets `maxDuration = 120` in
   `app/api/chat/route.ts` and `VERCEL_MAX_DURATION = 120` in `config.ts`. Hobby caps
   function duration lower than that. Either upgrade to Pro ($20/mo) or drop both to `60`.
   (likely) Deep reasoning + multiple tool calls can still time out at 60s — lower
   `DEFAULT_THINKING_LEVEL` and `MAX_STEPS` if so.
4. Set spend caps: Anthropic console monthly limit, Exa dashboard limit, Vercel Spend
   Management. The in-memory rate limiter resets on every cold start, so it is a soft
   layer only — add a Vercel Firewall rate-limit rule on `/api/chat` for a real ceiling.
5. Generate `SUMMARY_HMAC_SECRET` (`openssl rand -hex 32`) so compaction summaries can't
   be forged. Optional but do it.

---

## 7. Phase 5 — web search + live profiles (optional)

- `ENABLE_WEB_SEARCH=true` + `EXA_API_KEY`. Start with `EXA_SEARCH_TYPE="auto"` in
  `config.ts` to conserve credits; move to `"deep"` only if quality demands it.
- Web search is **scoped to `KB_SCOPE`** by prompt + tool description — the bot won't
  answer "who won the cricket match" even with web search on. That's deliberate cost control.
- `fetchOwnerProfiles` pulls your live LinkedIn/Scholar pages for "what's X up to lately"
  questions, and the prompt tells the model to trust the live profile over the (dated) KB
  when they disagree on current facts.

---

## 8. Gotchas the README half-buries

- **Pinecone index must be `llama-text-embed-v2` integrated inference.** Wrong embedding
  model = silent garbage retrieval. Re-ingesting is the only clean fix.
- The model's own citation numbers `[[N]]` are **thrown away** and renumbered by
  `lib/citations.ts` on both client and server. Don't "fix" citation numbering — it's
  deliberate and unit-tested.
- `content/` is gitignored on purpose. Published papers are copyrighted; your notes are
  private. Keep it that way.
- Notebooks must never be committed with keys filled in.
- `MAX_STEPS` must be `≥ MAX_KB_SEARCHES + MAX_WEB_SEARCHES + 2` or tool budgets break.

---

## 9. Pivot notes

**→ Lane A (public brand asset):** keep confidentiality prompts, rewrite `TONE_STYLE`
in your voice, ingest your public writing / project write-ups / talks, put real profile
URLs in `OWNER_PROFILE_SOURCES`, deploy on your domain.

**→ Lane C (product seed):** gut the "owner" framing in `prompts.ts` and `config.ts`,
rename to the product, point `KB_SCOPE` + the notebook at a niche audience's document
set (a professional body of knowledge, a course, a regulatory corpus), and the
parent-child RAG + citation-verification engine is your MVP. The moat is the curated
content and the ingestion quality, not the code.

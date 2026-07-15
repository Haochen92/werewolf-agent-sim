# Decision cards — nutri_ally + RAG_service

Local only (folder ignored via .git/info/exclude). Pre-filled from a code survey 2026-06-11 —
edit into your own voice and correct anything I inferred wrong (cards marked ⚠️ where the "why"
is my reconstruction, not something you told me).

**⚠️ POSITIONING RULE (before any card matters):** nutri_ally currently has NO AI assistant —
do not claim one on the site/resume/interviews until built. Honest framing today: full-stack
product engineering. RAG_service = separate document-RAG project (covers the doc-RAG interview
surface). Optional bounded build: a real nutri_ally assistant = chat route + function calling
over the EXISTING server actions (search_food / compute_targets / save_meal) — closes the
tool-use gap and makes the name honest. Also: remove or honestify the static "Intelligent
recommendations" carousel label.

---

## nutri_ally

### N1. Next.js server actions as the backend; the FastAPI service retired ⚠️

- **Chose:** BFF pattern — all data access through Next.js server components/actions + thin API
  routes; the separate FastAPI backend was started and then left dormant.
- **Realistic alternative:** finish the FastAPI backend (separate Python service, REST between
  front and back).
- **Why (reconstructed — verify):** with App Router, server actions already run trusted
  server-side code next to the ORM — a second service added a network hop, duplicate validation,
  and a second deploy unit while providing nothing the app needed (no heavy compute, no Python-only
  deps in the serving path).
- **What would change my mind:** real ML serving in the request path (model inference), another
  consumer needing the same API, or team scale wanting a typed contract boundary.
- **Probe I'm ready for:** "So you have dead code in the repo?" → yes, and the honest story is the
  decision to *stop* building it once server actions made it redundant — knowing when not to build
  a service is the senior version of knowing how to build one. (Consider deleting the stub before
  publishing the repo.)

### N2. Importing the 1M+ product OpenFoodFacts catalog into my own Postgres

- **Chose:** one-time ETL (Jupyter + Dask over a 6.2GB parquet) into a `ProductNutrientsInfo`
  table with 30+ nutrient columns; app queries it via Prisma (paginated search, nutrient
  filter/sort).
- **Realistic alternative:** call the public OpenFoodFacts API live per search.
- **Why:** the gallery needs SQL-shaped access — pagination, case-insensitive substring search,
  filter/sort on arbitrary nutrient columns — which a third-party REST API can't serve with
  acceptable latency or rate limits; owning the data also pins its quality (cleaning/unit
  normalization happened once, in the ETL).
- **What would change my mind:** needing fresh/live data (price, new products) → hybrid: own
  catalog + periodic re-sync job (the current ETL is one-shot, a known gap).
- **Probe I'm ready for:** "Your data is stale and the pipeline is a notebook." → true; the
  production version is the same transforms as a scheduled job + upsert; I'd also slim the 30+
  nullable columns to the queried subset.

### N3. NextAuth v5 multi-provider with account linking + JWT sessions ⚠️

- **Chose:** Google OAuth + GitHub OAuth + Resend magic-link, Prisma adapter, JWT session
  strategy, auto-linking new providers onto an existing user email, middleware route guard.
- **Realistic alternative:** managed auth (Clerk/Auth0) or single-provider.
- **Why (reconstructed — verify):** auth is a solved-but-instructive problem — the framework
  integration (adapter, callbacks, linking flow) is the learning value; managed auth hides
  exactly the parts worth understanding, and costs money at the margin.
- **What would change my mind:** a real product with compliance needs (SOC2, MFA policies) →
  managed provider immediately; auth is not where a product team should spend innovation budget.
- **Probe I'm ready for:** "JWT vs database sessions?" → JWT: no DB hit per request, but
  revocation is hard (logout-everywhere, banned users) — fine for this product; DB sessions when
  revocation matters.

### N4. Self-hosted OTel collector + Zipkin (over vendor APM / nothing) ⚠️

- **Chose:** OpenTelemetry instrumentation in Next.js → OTLP collector container → Zipkin UI,
  all in the same docker-compose.
- **Realistic alternative:** Vercel's built-in analytics / a paid APM / console.log.
- **Why:** vendor-neutral instrumentation (OTLP) means the backend is swappable; self-hosting
  keeps the whole stack reproducible in one compose file; and tracing knowledge transfers (the
  werewolf project uses the same discipline with Langfuse).
- **What would change my mind:** production traffic → managed backend for retention/alerting;
  the instrumentation layer wouldn't change, which is the point of OTel.
- **Probe I'm ready for:** "What did a trace actually catch?" → have ONE concrete debugging story
  ready (slow query, N+1, S3 latency). If none exists, say what you'd look for — don't invent.

### N5. App Router patterns: parallel + intercepted routes for the food-detail modal

- **Chose:** gallery uses a `@recommendation` parallel slot and intercepted routes so a product
  opens as a modal overlay while remaining a URL-addressable, server-rendered page on direct
  visit.
- **Realistic alternative:** client-state modal (one route, modal open/closed in React state).
- **Why:** deep-linking and share-ability for free (the modal IS a route), server rendering of
  detail content, browser back button behaves correctly.
- **What would change my mind:** the pattern's complexity is real (layout slots, default.tsx
  files); for an app without shareable detail views I'd use the boring client modal.
- **Probe I'm ready for:** "Explain how interception works." → route convention `(.)segment`
  renders in-place within the current layout on soft navigation; hard navigation gets the full
  page — know the soft/hard distinction.

### N6. Honest-gap card: no tests, no CI

- **Boundary statement, ready:** "True — it predates my eval-discipline phase; the werewolf
  project is where I built that muscle (95 tests, import-sweep gates, behavioral fingerprints).
  First things I'd add here: Playwright smoke on the three core flows, plus CI running
  typecheck + prisma migrate diff." Shows the growth arc instead of defending the gap.

---

## RAG_service

### R1. Hybrid retrieval (vector + BM25, RRF fusion) over pure vector search

- **Chose:** pgvector HNSW cosine (k=15) + ParadeDB BM25 keyword search, fused with reciprocal
  rank fusion (0.5/0.5 weights).
- **Realistic alternative:** pure dense vector search (the default everyone starts with).
- **Why:** the corpus is technical documentation (Mantine) — queries are keyword-heavy
  (component names, prop names like `ef_search`, exact API identifiers) where embeddings are
  weakest and lexical match is strongest; hybrid covers both query types. Evaluated with
  NDCG@k/precision against labeled queries rather than vibes.
- **What would change my mind:** the eval said so — if BM25 contributed nothing on the measured
  query set I'd drop the complexity. (Know your actual numbers from the notebook before claiming
  the direction.)
- **Probe I'm ready for:** "Why RRF over weighted score fusion?" → scores from different systems
  aren't calibrated to each other (cosine vs BM25 scale); RRF fuses *ranks*, sidestepping
  calibration entirely.

### R2. pgvector inside Postgres (ParadeDB) over a dedicated vector DB

- **Chose:** embeddings as a column in the same Postgres holding documents/chunks/eval tables;
  HNSW index; BM25 from the same engine.
- **Realistic alternative:** Pinecone/Weaviate/Qdrant.
- **Why:** one store = joins between chunks, metadata, and eval labels in plain SQL; transactional
  consistency between document and embedding writes; no second service to operate; BM25 and
  vectors in one engine is exactly what hybrid search wants. At this scale (one docs corpus) a
  dedicated vector DB adds ops cost and removes SQL.
- **What would change my mind:** ~10M+ vectors, high QPS, or needing managed scaling →
  dedicated store; the ingestion/retrieval interfaces are already separate modules, so the swap
  is contained.
- **Probe I'm ready for:** "HNSW vs IVFFlat? What does ef_search do?" → HNSW: graph-based,
  better recall/latency, slower builds; ef_search = search-time beam width, recall vs latency
  knob (I tuned it in the eval notebook — know the value you landed on).

### R3. Structure-aware chunking with context injection (over fixed-size splitting)

- **Chose:** custom markdown chunker — split on H2/H3 section boundaries, recursive character
  fallback (3000 chars, 300 overlap), section/topic context prepended to chunk text before
  embedding, SHA256 content-hash dedup.
- **Realistic alternative:** naive fixed-size chunks (the tutorial default).
- **Why:** docs have semantic structure; respecting section boundaries keeps a chunk about ONE
  thing (better embedding), and injecting the section path compensates for context lost by
  splitting ("this paragraph is about Button props" survives the cut). Hash dedup keeps
  re-ingestion idempotent.
- **What would change my mind:** corpus without structure (chat logs, OCR) → semantic/embedding-
  based splitting; very long structured docs → hierarchical (parent-child) chunks with
  small-to-big retrieval.
- **Probe I'm ready for:** "How did you pick 3000/300?" → honest answer: starting heuristic
  (~750 tokens, 10% overlap); the principled version is sweeping chunk size against the
  retrieval eval — name it as known future work if you didn't run the sweep.

### R4. Eval-first development: labeled queries + NDCG before building the API

- **Chose:** built gold-labeled query set (category/difficulty tagged), NDCG@k + precision@k +
  AP metrics, Langfuse tracing on every stage — while the REST API is still just /health.
- **Realistic alternative:** build the chat endpoint first, eyeball answers, ship.
- **Why:** retrieval quality IS the product; the API is an afternoon once retrieval is proven.
  Tuning (ef_search, fusion weights, chunking) against a fixed labeled set turns every change
  into a measured delta instead of a vibe. Same philosophy as the werewolf eval program — this is
  a consistent personal methodology across projects, say it that way.
- **What would change my mind:** nothing for the order; but the eval set is small and
  self-labeled — scaling it needs the panel/blinding discipline from the werewolf labelling work.
- **Probe I'm ready for:** "Your gold labels — who labeled them and how do you know they're
  right?" → self-labeled, single annotator, known limitation; the werewolf project is where I
  built the multi-judge + human-anchor methodology that fixes exactly this.

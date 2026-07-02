# FC Edge — Roadmap

How the full product spec maps onto phases. **Phase 0 is what ships in this repo today.**

## Phase 0 — Foundation ✅ (this repo)

- Monorepo, Docker stack, SQLite/Postgres portability, seeded demo data.
- Dashboard, AI rating engine, Market Scanner, Live Market search, Player
  Intelligence page with interactive charts, SBC Centre.
- **AI SBC Solver** — real squad-rating + chemistry + formation position-slotting
  with cheapest / highest-rated / least-club-loss objectives, protect flags,
  a shopping list, one-click completion (spend + consume) and whole-set solving.
- **Club Manager** — imported club, duplicates, fodder value, protection flags.
- **Live market** — WebSocket price tape + alert fan-out (in-process ticker in
  dev; Celery beat + Redis pub/sub in production).
- **AI Coach** — natural-language answers grounded in live market + club data,
  LLM-backed when a key is present, deterministic heuristic otherwise.
- Premium dark/glass design system, PWA manifest, mobile-first layout.

## Phase 1 — Live data & realtime

- ✅ **Price ingest pipeline** (Celery beat) + in-process dev ticker writing
  `price_history` and firing alerts continuously.
- ✅ **WebSockets** for live price ticks and alert triggers (Redis pub/sub fan-out).
- **Materialised views** for hourly/daily/weekly/monthly graphs + scanner.
- **Redis caching** on hot endpoints; infinite scroll on market lists.
- Real market data source; price prediction model feeding "expected movement / peak".

## Phase 2 — Accounts, portfolio & alerts

- **Auth**: Google, Apple, Discord, Email.
- Personal **portfolio** with purchase tracking, ROI, tax, performance charts.
- **Trade logging** with success rate + average ROI analytics.
- **Price alerts** with Firebase / Apple Push / Web Push fan-out.
- **Stripe** premium subscription (£2.99/mo) gating unlimited AI/alerts/solves.

## Phase 3 — Club & squad intelligence

- **Club import** from EA (live) → evolution candidates, recommended sales
  (the club *model* and manual/seeded club already ship in Phase 0).
- **AI SBC Solver — v2**: exact formation slotting, ILP/constraint back-end,
  one-click auto-buy execution, repeat-solver for entire SBC sets
  (the cheapest/highest-rated/protect solver ships in Phase 0).
- **Squad Builder** with chemistry / role / PlayStyle optimisers and meta templates.
- **Evolution Centre** with projected ratings and best-value evolution finder.

## Phase 4 — Coach, content & community

- ✅ **AI Coach** (LLM over live market data, offline heuristic fallback):
  "What should I invest in?", "How do I make 500k?". Next: conversation memory,
  tool-use to place alerts / trigger solves directly from chat.
- **Roadmap Generator**: personalised daily/weekly tasks, coin & reward forecast.
- **News Centre**, **Pack Centre** (odds, EV, simulator), **Objectives** tracker.
- **Community**: profiles, follows, trading/investment posts, premium creators.

## Phase 5 — Platform & ecosystem

- **Public paid API** (tiered, rate-limited) for third-party developers.
- Native **iOS / Android** shells over the shared web core.
- Local-LLM option for on-device AI; PostHog analytics; Cloudinary media.

---

### Design north star

The Bloomberg Terminal of EA Sports FC — users open FC Edge not because they *need*
a price, but because it tells them **what to buy, what to sell, and which SBCs are
worth it**. Every feature must save time, make coins, or improve the club.

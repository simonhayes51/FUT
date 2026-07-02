<div align="center">

# ⚡ FC Edge

**The trading terminal for EA Sports FC.**

Market intelligence, AI ratings and squad tools in one premium product — built to be
the app you open *before* FUTBIN, FUT.GG or FUTWIZ.

</div>

---

## What this repository is

This is the **foundation build** of FC Edge: a working, end-to-end vertical slice of
the platform described in the product spec, architected so the remaining features
(see the [Roadmap](docs/ROADMAP.md)) slot in without rework.

What runs today, fully wired frontend → API → database:

| Feature | Status |
| --- | --- |
| **Dashboard** — club value, coin balance, profit, watchlist/alert counters, AI assistant briefing | ✅ |
| **AI Market Intelligence** — explainable 0–100 investment rating, confidence, risk, ROI, buy/sell/peak targets, reasons | ✅ |
| **Market Scanner** — best investments, fastest risers/fallers, undervalued, highest volume, highest ROI | ✅ |
| **Live Market** — player search + league/rating filters | ✅ |
| **Player Intelligence page** — interactive price chart (1D/1W/1M/All), lowest/highest BIN, volume, volatility, supply/demand | ✅ |
| **SBC Centre** — cost, pack value, net profit, value rating, expiry, "worth completing?" verdict | ✅ |
| **AI SBC Solver** — real squad-building engine (FUT squad-rating + FC 24/25 chemistry) that solves each SBC for *cheapest / highest-rated / least club value lost*, honours protect-icons/favourites/first-owner, and produces a shopping list of missing cards | ✅ |
| **Club Manager** — imported club with duplicates, fodder value, protection flags (the solver's raw material) | ✅ |
| **Premium design system** — dark, glassmorphism, purple/blue gradients, neon accents, Framer Motion, mobile-first, PWA manifest | ✅ |

Everything is backed by a realistic **seeded dataset** (30 players, ~7k price points,
SBCs, a demo portfolio) so the product is fully explorable with zero configuration.

## Quick start

### Option A — Docker (full Postgres + Redis stack)

```bash
docker compose up --build
# Web  → http://localhost:3000
# API  → http://localhost:8000/api/v1/health
# Docs → http://localhost:8000/docs
```

### Option B — Local dev (SQLite, no services needed)

```bash
# API
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed              # create + populate fcedge.db
uvicorn app.main:app --reload   # http://localhost:8000

# Web (new terminal)
cd apps/web
npm install
npm run dev                     # http://localhost:3000
```

## Architecture at a glance

```
apps/
  api/   FastAPI + SQLAlchemy + Pydantic
         └─ ai.py           deterministic, explainable rating engine
         └─ solver.py       AI SBC Solver — squad-rating + chemistry + search
         └─ models.py       players · price_history · analytics · users
                            · investments · trades · watchlist · alerts
                            · sbcs · club_players
         └─ routers/        dashboard · market · players · sbc · club
         └─ seed.py         reproducible demo dataset
  web/   Next.js 14 (App Router) + TS + Tailwind + Framer Motion
         + React Query + Zustand
docs/    ARCHITECTURE.md · ROADMAP.md
```

The AI rating engine is **deterministic and explainable** — it scores the same
signals a human trader watches (momentum, supply/demand, volatility, SBC catalysts)
so every rating can answer *"why 93/100?"*. An optional OpenAI key layers a
natural-language AI Coach on top; without it the product is fully functional offline.

See **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for the data model and scaling
plan, and **[docs/ROADMAP.md](docs/ROADMAP.md)** for how the full spec maps to phases.

## Tech stack

**Frontend** Next.js · React · TypeScript · TailwindCSS · Framer Motion · React Query · Zustand
**Backend** FastAPI · Python · PostgreSQL · Redis · (Celery/WebSockets — Phase 1)
**Infra** Docker · Railway · Cloudflare

## Licence

MIT — see [LICENSE](LICENSE).

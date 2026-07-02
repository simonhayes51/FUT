# FC Edge — Architecture

## Principles

1. **One shared contract.** The FastAPI Pydantic schemas (`apps/api/app/schemas.py`)
   are mirrored 1:1 by the TypeScript types (`apps/web/lib/types.ts`). The frontend
   never guesses the shape of a response.
2. **Explainable intelligence.** Every AI number is derived from transparent signals,
   never a black box. This is a trust feature: users act on ratings, so ratings must
   justify themselves.
3. **Runs anywhere, unchanged.** The same code boots on SQLite with zero services
   (first-run / CI) and on Postgres + Redis in production, switched by `DATABASE_URL`.

## Services

```
┌──────────┐     HTTPS/JSON      ┌──────────┐     SQL      ┌────────────┐
│  Next.js │ ──────────────────▶ │ FastAPI  │ ───────────▶ │ PostgreSQL │
│  (Web /  │ ◀────────────────── │  API     │ ◀─────────── │            │
│   PWA)   │                     │          │              └────────────┘
└──────────┘                     │          │     cache    ┌────────────┐
                                 │          │ ───────────▶ │   Redis    │
                                 └────┬─────┘              └────────────┘
                                      │ enqueue
                                      ▼
                            ┌───────────────────┐   (Phase 1)
                            │  Celery workers   │  price ingest · analytics
                            │                   │  refresh · alert fan-out
                            └───────────────────┘
```

## Data model

| Table | Purpose | Notes |
| --- | --- | --- |
| `players` | Card catalogue + denormalised latest price | `price`/`price_change_pct` cached so list pages never join history |
| `price_history` | (player, timestamp) BIN observations | Highest-volume table. Prod: monthly partitions + materialised views for hourly/daily/weekly/monthly graphs |
| `market_analytics` | Derived snapshot per player | Refreshed by Celery; feeds the AI engine and scanner |
| `users` | Accounts + premium flag + coin balance | Auth providers land in Phase 2 |
| `investments` | Open positions | Drives club value + portfolio |
| `trades` | Closed buy→sell cycles | `net_profit` applies EA's 5% tax |
| `watchlist_items` / `price_alerts` | User market tracking | Alert fan-out via Celery + push |
| `sbcs` | SBC catalogue | Cost, pack value, value rating, expiry + structured solve constraints (formation, min rating, min chemistry) |
| `club_players` | The user's owned cards | Quantity + protection flags; the AI SBC Solver's raw material |

## The AI rating engine (`app/ai.py`)

`rate_player()` combines four signals into a 0–100 score:

- **Demand pressure** `demand − supply` — the classic "about to rise" signal.
- **Momentum** — trend of the recent BIN series.
- **Structural catalysts** — upcoming SBC requirement, meta rating premium.
- **Volatility** — dampens confidence and raises the risk band.

It returns a `verdict` (BUY/HOLD/SELL/AVOID), confidence, risk, time horizon,
ROI (net of 5% tax), suggested buy/sell/peak prices and a human-readable list of
reasons. Because it is deterministic it is trivially testable and reproducible.

## The AI SBC Solver (`app/solver.py`)

Two game mechanics are modelled exactly: **squad rating** (FUT's
above-average-weighted formula) and **chemistry** (the FC 24/25 count-based
club/league/nation model, capped at 33). Given a candidate pool (the user's club
at zero coin cost, plus market fodder to buy), `solve()` seeds the cheapest
eleven and runs cost-aware local-search swaps to reach the SBC's required rating
and chemistry, optimising for one of three objectives — *cheapest*,
*highest_rating*, *min_club_loss* — while honouring protect-icons/favourites/
first-owner flags. It is deterministic (stable sort + fixed tie-breaks) and
returns the squad, the coins-to-buy shopping list, club value consumed, and any
unmet constraints. Production swaps the heuristic for an ILP/constraint solver
behind the identical interface.

## Scaling notes (how today's slice grows to "billions of price records")

- **Ingest**: a Celery beat schedule polls the market and bulk-inserts into
  `price_history`; the denormalised `players.price` columns are updated in the same
  transaction.
- **Reads**: the scanner and graphs move from per-request Python ranking to
  **materialised views** refreshed on the analytics cadence, cached in Redis.
- **Realtime**: WebSocket channels push price ticks and alert triggers.
- **Partitioning**: `price_history` is range-partitioned by month; old partitions are
  rolled to cold storage while views keep aggregates hot.
- **API tiering**: the same endpoints, rate-limited and keyed, become the paid public
  API described in the spec.

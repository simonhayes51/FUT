"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ArrowLeft, Check, Loader2, Sparkles, X } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { RatingBadge } from "@/components/ui";
import { coins } from "@/lib/format";
import type { SolveObjective, SolveOptions, SolveResult, SquadSlot } from "@/lib/types";

const OBJECTIVES: { key: SolveObjective; label: string; hint: string }[] = [
  { key: "cheapest", label: "Cheapest", hint: "Fewest coins out of pocket" },
  { key: "min_club_loss", label: "Protect Club", hint: "Least club value lost" },
  { key: "highest_rating", label: "Highest Rated", hint: "Best squad possible" },
];

const DEFAULTS: SolveOptions = {
  objective: "cheapest",
  use_club: true,
  buy_missing: true,
  protect_icons: true,
  protect_favourites: true,
  protect_first_owner: false,
};

export default function SolvePage() {
  const { id } = useParams<{ id: string }>();
  const [opts, setOpts] = useState<SolveOptions>(DEFAULTS);

  const { data: sbc } = useQuery({ queryKey: ["sbc", id], queryFn: () => api.sbc(id) });
  const solve = useMutation({ mutationFn: (o: SolveOptions) => api.solve(id, o) });

  // Auto-solve on first load so the page never sits empty.
  useEffect(() => {
    solve.mutate(DEFAULTS);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const result = solve.data;

  return (
    <div className="space-y-6">
      <Link href="/sbc" className="inline-flex items-center gap-1.5 text-sm text-white/50 hover:text-white">
        <ArrowLeft className="h-4 w-4" /> Back to SBC Solver
      </Link>

      <header className="glass p-5">
        <div className="flex items-center gap-2 text-sm font-semibold text-brand-violet">
          <Sparkles className="h-4 w-4" /> AI SBC Solver
        </div>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">{sbc?.name ?? "…"}</h1>
        {sbc && (
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-white/50">
            <span>{sbc.formation}</span>
            <span>Rating ≥ <b className="text-white/80">{sbc.min_rating}</b></span>
            <span>Chemistry ≥ <b className="text-white/80">{sbc.min_chemistry}</b></span>
            <span>Reward: {sbc.reward}</span>
          </div>
        )}
      </header>

      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        {/* Options */}
        <aside className="glass h-fit p-5">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/60">
            Optimise for
          </h2>
          <div className="flex flex-col gap-2">
            {OBJECTIVES.map((o) => (
              <button
                key={o.key}
                onClick={() => setOpts((s) => ({ ...s, objective: o.key }))}
                className={`rounded-xl border p-3 text-left transition ${
                  opts.objective === o.key
                    ? "border-brand-violet/50 bg-brand-violet/15"
                    : "border-white/10 bg-black/20 hover:bg-white/5"
                }`}
              >
                <div className="text-sm font-semibold">{o.label}</div>
                <div className="text-xs text-white/45">{o.hint}</div>
              </button>
            ))}
          </div>

          <h2 className="mb-2 mt-5 text-sm font-semibold uppercase tracking-wide text-white/60">
            Protect
          </h2>
          <Toggle label="Icons" value={opts.protect_icons} onChange={(v) => setOpts((s) => ({ ...s, protect_icons: v }))} />
          <Toggle label="Favourites" value={opts.protect_favourites} onChange={(v) => setOpts((s) => ({ ...s, protect_favourites: v }))} />
          <Toggle label="First owners" value={opts.protect_first_owner} onChange={(v) => setOpts((s) => ({ ...s, protect_first_owner: v }))} />

          <h2 className="mb-2 mt-5 text-sm font-semibold uppercase tracking-wide text-white/60">
            Sources
          </h2>
          <Toggle label="Use my club" value={opts.use_club} onChange={(v) => setOpts((s) => ({ ...s, use_club: v }))} />
          <Toggle label="Buy missing players" value={opts.buy_missing} onChange={(v) => setOpts((s) => ({ ...s, buy_missing: v }))} />

          <button
            onClick={() => solve.mutate(opts)}
            disabled={solve.isPending}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-brand-gradient py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
          >
            {solve.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Solve
          </button>
        </aside>

        {/* Result */}
        <section className="space-y-4">
          {solve.isPending && !result && <div className="glass h-64 animate-pulse" />}
          {result && <ResultView result={result} />}
        </section>
      </div>
    </div>
  );
}

function ResultView({ result }: { result: SolveResult }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      {/* Summary */}
      <div className="glass shadow-glow p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {result.feasible ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-neon-green/15 px-3 py-1 text-sm font-semibold text-neon-green">
                <Check className="h-4 w-4" /> Solution found
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-neon-red/15 px-3 py-1 text-sm font-semibold text-neon-red">
                <X className="h-4 w-4" /> Not solvable
              </span>
            )}
          </div>
          {result.to_buy.length > 0 && (
            <button className="rounded-xl bg-white/5 px-3 py-1.5 text-xs font-semibold text-white/80 hover:bg-white/10">
              Auto-buy {result.to_buy.length} missing →
            </button>
          )}
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="Squad Rating" value={`${result.squad_rating}`} ok={result.squad_rating >= result.required_rating} target={`≥ ${result.required_rating}`} />
          <Stat label="Chemistry" value={`${result.chemistry}`} ok={result.chemistry >= result.required_chemistry} target={`≥ ${result.required_chemistry}`} />
          <Stat label="Coins to Buy" value={coins(result.total_cost)} tone="amber" />
          <Stat label="Club Value Used" value={coins(result.club_value_used)} tone="violet" />
        </div>

        {!result.feasible && (
          <ul className="mt-3 space-y-1 text-sm text-neon-red">
            {result.unmet.map((u, i) => (
              <li key={i}>• {u}</li>
            ))}
          </ul>
        )}
      </div>

      {/* Squad grid */}
      <div className="glass p-5">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/60">
          Suggested Squad
        </h2>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {result.squad.map((s, i) => (
            <SquadCard key={`${s.player_id}-${i}`} slot={s} />
          ))}
        </div>
      </div>

      {/* To buy */}
      {result.to_buy.length > 0 && (
        <div className="glass p-5">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/60">
            Shopping List ({result.to_buy.length})
          </h2>
          <div className="flex flex-col gap-2">
            {result.to_buy.map((s, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-black/20 px-3 py-2">
                <span className="text-sm">{s.rating} · {s.name}</span>
                <span className="text-sm font-semibold text-neon-amber">{coins(s.cost)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}

function SquadCard({ slot }: { slot: SquadSlot }) {
  const owned = slot.source === "club";
  return (
    <div className="flex items-center gap-2.5 rounded-xl border border-white/10 bg-black/20 p-2.5">
      <RatingBadge
        player={{
          id: slot.player_id,
          name: slot.name,
          rating: slot.rating,
          position: slot.position,
          club: slot.club,
          league: slot.league,
          nation: slot.nation,
          card_type: slot.card_type,
          image_url: null,
          price: slot.market_value,
          price_change_pct: 0,
        }}
      />
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium">{slot.name}</div>
        <div className="truncate text-[11px] text-white/40">{slot.league}</div>
      </div>
      <span
        className={`rounded-full px-1.5 py-0.5 text-[9px] font-semibold uppercase ${
          owned ? "bg-neon-green/15 text-neon-green" : "bg-neon-amber/15 text-neon-amber"
        }`}
      >
        {owned ? "Club" : "Buy"}
      </span>
    </div>
  );
}

function Stat({
  label,
  value,
  ok,
  target,
  tone,
}: {
  label: string;
  value: string;
  ok?: boolean;
  target?: string;
  tone?: "amber" | "violet";
}) {
  const color =
    ok === undefined
      ? tone === "amber"
        ? "text-neon-amber"
        : "text-brand-violet"
      : ok
        ? "text-neon-green"
        : "text-neon-red";
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-3">
      <div className="text-[11px] uppercase tracking-wide text-white/45">{label}</div>
      <div className={`mt-0.5 text-lg font-bold ${color}`}>{value}</div>
      {target && <div className="text-[10px] text-white/40">{target}</div>}
    </div>
  );
}

function Toggle({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      onClick={() => onChange(!value)}
      className="flex w-full items-center justify-between py-1.5 text-sm text-white/80"
    >
      {label}
      <span
        className={`relative h-5 w-9 rounded-full transition ${
          value ? "bg-brand-violet" : "bg-white/15"
        }`}
      >
        <span
          className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-all ${
            value ? "left-4" : "left-0.5"
          }`}
        />
      </span>
    </button>
  );
}

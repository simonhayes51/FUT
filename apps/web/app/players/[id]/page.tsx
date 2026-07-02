"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ArrowLeft, Sparkles } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";
import { PriceChart } from "@/components/PriceChart";
import { ChangeTag, RatingBadge } from "@/components/ui";
import { coins, coinsFull, scoreColor, verdictColor } from "@/lib/format";
import type { PricePoint } from "@/lib/types";

const RANGES = [
  { key: "1D", hours: 24 },
  { key: "1W", hours: 24 * 7 },
  { key: "1M", hours: 24 * 30 },
  { key: "ALL", hours: 99999 },
] as const;

export default function PlayerPage() {
  const { id } = useParams<{ id: string }>();
  const [range, setRange] = useState<(typeof RANGES)[number]["key"]>("1M");
  const { data: p, isLoading } = useQuery({
    queryKey: ["player", id],
    queryFn: () => api.player(id),
  });

  const history = useMemo(() => {
    if (!p) return [] as PricePoint[];
    const hours = RANGES.find((r) => r.key === range)!.hours;
    const cutoff = Date.now() - hours * 3_600_000;
    return p.history.filter((h) => new Date(h.recorded_at).getTime() >= cutoff);
  }, [p, range]);

  if (isLoading) {
    return <div className="glass h-96 animate-pulse" />;
  }
  if (!p) return null;

  const ai = p.ai;
  const a = p.analytics;

  return (
    <div className="space-y-6">
      <Link href="/market" className="inline-flex items-center gap-1.5 text-sm text-white/50 hover:text-white">
        <ArrowLeft className="h-4 w-4" /> Back to market
      </Link>

      {/* Header */}
      <div className="glass flex flex-wrap items-center gap-4 p-5">
        <div className="scale-125">
          <RatingBadge player={p} />
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold tracking-tight">{p.name}</h1>
          <p className="text-sm text-white/50">
            {p.rating} {p.position} · {p.club} · {p.nation} · {p.card_type}
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold">{coinsFull(p.price)}</div>
          <ChangeTag value={p.price_change_pct} />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Chart */}
        <div className="glass p-5 lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-white/60">
              Price History
            </h2>
            <div className="flex gap-1 rounded-lg border border-white/10 bg-black/20 p-1">
              {RANGES.map((r) => (
                <button
                  key={r.key}
                  onClick={() => setRange(r.key)}
                  className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${
                    range === r.key ? "bg-brand-gradient text-white" : "text-white/50 hover:text-white"
                  }`}
                >
                  {r.key}
                </button>
              ))}
            </div>
          </div>
          <PriceChart data={history} />
          {a && (
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Metric label="Lowest BIN" value={coins(a.lowest_bin)} />
              <Metric label="Highest BIN" value={coins(a.highest_bin)} />
              <Metric label="Volume" value={a.volume.toLocaleString("en-GB")} />
              <Metric label="Volatility" value={`${Math.round(a.volatility * 100)}%`} />
            </div>
          )}
        </div>

        {/* AI intelligence */}
        {ai && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass shadow-glow p-5"
          >
            <div className="mb-4 flex items-center gap-2 text-sm font-semibold">
              <Sparkles className="h-4 w-4 text-brand-violet" /> AI Investment Rating
            </div>

            <div className="flex items-center gap-4">
              <ScoreRing score={ai.score} />
              <div>
                <div className={`text-xl font-bold ${verdictColor(ai.verdict)}`}>{ai.verdict}</div>
                <div className="text-xs text-white/50">
                  {ai.confidence}% confidence · {ai.risk} risk
                </div>
                <div className="text-xs text-white/50">{ai.time_horizon}</div>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-3 gap-2 text-center">
              <SuggestBox label="Buy" value={coins(ai.suggested_buy)} tone="green" />
              <SuggestBox label="Sell" value={coins(ai.suggested_sell)} tone="red" />
              <SuggestBox label="Peak" value={coins(ai.expected_peak)} tone="violet" />
            </div>

            <div className="mt-4 rounded-xl border border-white/10 bg-black/20 p-3">
              <div className="text-xs font-semibold text-white/60">Expected ROI</div>
              <div className={`text-lg font-bold ${ai.expected_roi_pct >= 0 ? "text-neon-green" : "text-neon-red"}`}>
                {ai.expected_roi_pct > 0 ? "+" : ""}
                {ai.expected_roi_pct}%
              </div>
            </div>

            <div className="mt-4">
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-white/50">
                Why this rating
              </div>
              <ul className="space-y-1.5">
                {ai.reasons.map((r, i) => (
                  <li key={i} className="flex gap-2 text-sm text-white/80">
                    <span className="text-brand-violet">›</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        )}
      </div>

      {/* Supply / demand bars */}
      {a && (
        <div className="glass p-5">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/60">
            Supply &amp; Demand
          </h2>
          <Bar label="Demand" value={a.demand} tone="green" />
          <Bar label="Supply" value={a.supply} tone="blue" />
          <div className="mt-3 flex gap-4 text-xs text-white/50">
            <span>Buy score <b className={scoreColor(a.buy_score)}>{a.buy_score}</b></span>
            <span>Sell score <b className="text-neon-red">{a.sell_score}</b></span>
            <span>Hold score <b className="text-neon-amber">{a.hold_score}</b></span>
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-3">
      <div className="text-[11px] uppercase tracking-wide text-white/45">{label}</div>
      <div className="mt-0.5 text-sm font-bold">{value}</div>
    </div>
  );
}

function SuggestBox({ label, value, tone }: { label: string; value: string; tone: string }) {
  const color = { green: "text-neon-green", red: "text-neon-red", violet: "text-brand-violet" }[tone];
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-2.5">
      <div className="text-[11px] text-white/45">{label}</div>
      <div className={`text-sm font-bold ${color}`}>{value}</div>
    </div>
  );
}

function ScoreRing({ score }: { score: number }) {
  const r = 30;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - score / 100);
  const color = score >= 75 ? "#34d399" : score >= 55 ? "#fbbf24" : "#fb7185";
  return (
    <div className="relative h-20 w-20 shrink-0">
      <svg viewBox="0 0 80 80" className="h-20 w-20 -rotate-90">
        <circle cx="40" cy="40" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="7" />
        <circle
          cx="40"
          cy="40"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold" style={{ color }}>{score}</span>
        <span className="text-[9px] text-white/40">/100</span>
      </div>
    </div>
  );
}

function Bar({ label, value, tone }: { label: string; value: number; tone: string }) {
  const bg = { green: "bg-neon-green", blue: "bg-brand-blue" }[tone];
  return (
    <div className="mb-2">
      <div className="mb-1 flex justify-between text-xs text-white/60">
        <span>{label}</span>
        <span>{value}/100</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/5">
        <div className={`h-full rounded-full ${bg}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

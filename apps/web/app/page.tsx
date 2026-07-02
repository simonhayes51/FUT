"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Bell, Eye, Sparkles, TrendingUp } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { coins, coinsFull, scoreColor } from "@/lib/format";
import { LiveTape } from "@/components/LiveTape";
import { PlayerRow, ScannerColumn, StatCard } from "@/components/ui";

export default function DashboardPage() {
  const dash = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard });
  const scanner = useQuery({ queryKey: ["scanner"], queryFn: () => api.scanner(8) });

  if (dash.isError) {
    return <ApiHint />;
  }

  const d = dash.data;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
            Good evening, <span className="gradient-text">Simon</span>
          </h1>
          <p className="text-sm text-white/50">
            Here&apos;s what moved in the market today.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-white/50">
          <Link href="/coach" className="chip glass-hover">
            Ask the AI Coach
          </Link>
          <Link href="/market" className="chip glass-hover">
            Open Market
          </Link>
        </div>
      </header>

      <LiveTape />

      {/* AI assistant briefing */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass shadow-glow relative overflow-hidden p-5"
      >
        <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
          <Sparkles className="h-4 w-4 text-brand-violet" />
          AI Personal Assistant
        </div>
        <ul className="space-y-1.5">
          {(d?.assistant_briefing ?? skeletonLines).map((line, i) => (
            <li key={i} className="flex gap-2 text-sm text-white/80">
              <span className="text-brand-violet">›</span>
              {typeof line === "string" ? line : <Shimmer />}
            </li>
          ))}
        </ul>
      </motion.div>

      {/* Stat row */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Club Value"
          value={d ? `${coins(d.club_value)}` : "—"}
          sub={<span className="text-white/45">Open positions: {d?.open_positions ?? 0}</span>}
          accent="purple"
          delay={0.02}
        />
        <StatCard
          label="Coin Balance"
          value={d ? coins(d.coin_balance) : "—"}
          sub={<span className="text-white/45">{d ? coinsFull(d.coin_balance) : ""}</span>}
          accent="blue"
          delay={0.06}
        />
        <StatCard
          label="Profit This Week"
          value={d ? `${coins(d.profit_this_week)}` : "—"}
          sub={<span className="text-neon-green">Realised</span>}
          accent="green"
          delay={0.1}
        />
        <StatCard
          label="Profit This Month"
          value={d ? `${coins(d.profit_this_month)}` : "—"}
          sub={<span className="text-neon-green">Net of 5% tax</span>}
          accent="green"
          delay={0.14}
        />
      </div>

      {/* Quick counters */}
      <div className="grid grid-cols-3 gap-4">
        <MiniStat icon={<Eye className="h-4 w-4" />} label="Watchlist" value={d?.watchlist_count ?? 0} />
        <MiniStat icon={<Bell className="h-4 w-4" />} label="Active Alerts" value={d?.active_alerts ?? 0} />
        <MiniStat icon={<TrendingUp className="h-4 w-4" />} label="Trending" value={d?.trending.length ?? 0} />
      </div>

      {/* AI recommendations + trending */}
      <div className="grid gap-6 lg:grid-cols-3">
        <section className="lg:col-span-2">
          <SectionTitle>AI Recommendations</SectionTitle>
          <div className="grid gap-3 sm:grid-cols-2">
            {(d?.top_investments ?? []).map((row) => (
              <PlayerRow
                key={row.player.id}
                player={row.player}
                right={
                  <div className="text-right">
                    <div className={`text-lg font-bold ${scoreColor(row.metric)}`}>
                      {Math.round(row.metric)}
                    </div>
                    <div className="text-[11px] font-semibold text-white/50">
                      {row.label}
                    </div>
                  </div>
                }
              />
            ))}
          </div>
        </section>

        <section>
          <SectionTitle>Trending Now</SectionTitle>
          <div className="flex flex-col gap-3">
            {(d?.trending ?? []).slice(0, 5).map((p) => (
              <PlayerRow key={p.id} player={p} />
            ))}
          </div>
        </section>
      </div>

      {/* Market scanner */}
      <section>
        <SectionTitle>Market Scanner</SectionTitle>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {scanner.data && (
            <>
              <ScannerColumn title="Best Investments" emoji="🧠" rows={scanner.data.best_investments} format="score" />
              <ScannerColumn title="Fastest Risers" emoji="🚀" rows={scanner.data.fastest_risers} format="pct" />
              <ScannerColumn title="Fastest Fallers" emoji="📉" rows={scanner.data.fastest_fallers} format="pct" />
              <ScannerColumn title="Most Undervalued" emoji="💎" rows={scanner.data.most_undervalued} format="raw" />
              <ScannerColumn title="Highest Volume" emoji="🔥" rows={scanner.data.highest_volume} format="raw" />
              <ScannerColumn title="Highest ROI Potential" emoji="💰" rows={scanner.data.highest_profit} format="pct" />
            </>
          )}
        </div>
      </section>
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/60">{children}</h2>;
}

function MiniStat({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="glass flex items-center gap-3 p-3.5">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 text-brand-violet">
        {icon}
      </div>
      <div>
        <div className="text-lg font-bold leading-none">{value}</div>
        <div className="text-xs text-white/45">{label}</div>
      </div>
    </div>
  );
}

const skeletonLines = [null, null, null];
function Shimmer() {
  return <span className="inline-block h-4 w-64 max-w-full animate-pulse rounded bg-white/10" />;
}

function ApiHint() {
  return (
    <div className="glass mx-auto mt-20 max-w-lg p-8 text-center">
      <h2 className="text-lg font-bold">Can&apos;t reach the FC Edge API</h2>
      <p className="mt-2 text-sm text-white/60">
        Start the backend with <code className="rounded bg-white/10 px-1.5 py-0.5">docker compose up</code>{" "}
        or run the API on <code className="rounded bg-white/10 px-1.5 py-0.5">:8000</code>. See the README for setup.
      </p>
    </div>
  );
}

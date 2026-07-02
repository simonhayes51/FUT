"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import type { PlayerSummary, ScannerRow } from "@/lib/types";
import { coins, pct, scoreColor } from "@/lib/format";

// Card-type accent used for the rating badge glow.
function cardAccent(type: string) {
  if (type === "Icon") return "from-amber-300/30 to-yellow-500/10 text-amber-200";
  if (type.includes("TOTW")) return "from-zinc-200/20 to-zinc-500/10 text-zinc-100";
  return "from-brand-purple/25 to-brand-blue/10 text-white";
}

export function RatingBadge({ player }: { player: PlayerSummary }) {
  return (
    <div
      className={`flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-xl bg-gradient-to-br ${cardAccent(
        player.card_type,
      )} border border-white/10`}
    >
      <span className="text-base font-bold leading-none">{player.rating}</span>
      <span className="text-[9px] font-medium leading-none opacity-70">
        {player.position}
      </span>
    </div>
  );
}

export function ChangeTag({ value }: { value: number }) {
  const up = value >= 0;
  return (
    <span
      className={`inline-flex items-center gap-0.5 text-sm font-semibold ${
        up ? "text-neon-green" : "text-neon-red"
      }`}
    >
      {up ? (
        <ArrowUpRight className="h-3.5 w-3.5" />
      ) : (
        <ArrowDownRight className="h-3.5 w-3.5" />
      )}
      {pct(value)}
    </span>
  );
}

export function PlayerRow({
  player,
  right,
}: {
  player: PlayerSummary;
  right?: React.ReactNode;
}) {
  return (
    <Link
      href={`/players/${player.id}`}
      className="glass glass-hover flex items-center gap-3 p-3"
    >
      <RatingBadge player={player} />
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">{player.name}</div>
        <div className="truncate text-xs text-white/45">
          {player.club} · {player.league}
        </div>
      </div>
      <div className="text-right">
        {right ?? (
          <>
            <div className="text-sm font-semibold">{coins(player.price)}</div>
            <ChangeTag value={player.price_change_pct} />
          </>
        )}
      </div>
    </Link>
  );
}

export function ScannerColumn({
  title,
  emoji,
  rows,
  format = "coins",
}: {
  title: string;
  emoji: string;
  rows: ScannerRow[];
  format?: "coins" | "pct" | "score" | "raw";
}) {
  const fmt = (n: number) => {
    if (format === "pct") return pct(n);
    if (format === "score") return `${Math.round(n)}`;
    if (format === "raw") return n.toLocaleString("en-GB");
    return coins(n);
  };
  return (
    <div className="glass p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <span>{emoji}</span>
        {title}
      </div>
      <div className="flex flex-col gap-2">
        {rows.slice(0, 6).map((r, i) => (
          <Link
            key={`${r.player.id}-${i}`}
            href={`/players/${r.player.id}`}
            className="flex items-center gap-2.5 rounded-lg px-2 py-1.5 transition hover:bg-white/5"
          >
            <span className="w-4 text-xs font-semibold text-white/30">
              {i + 1}
            </span>
            <RatingBadge player={r.player} />
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium">{r.player.name}</div>
              <div className="truncate text-[11px] text-white/40">
                {coins(r.player.price)} coins
              </div>
            </div>
            <span
              className={`text-sm font-semibold ${
                format === "score" ? scoreColor(r.metric) : "text-white/80"
              }`}
            >
              {fmt(r.metric)}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}

export function StatCard({
  label,
  value,
  sub,
  accent = "purple",
  delay = 0,
}: {
  label: string;
  value: string;
  sub?: React.ReactNode;
  accent?: "purple" | "blue" | "green";
  delay?: number;
}) {
  const ring = {
    purple: "shadow-glow",
    blue: "shadow-glow-blue",
    green: "shadow-[0_0_40px_-8px_rgba(52,211,153,0.4)]",
  }[accent];
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay }}
      className={`glass ${ring} p-4`}
    >
      <div className="text-xs font-medium uppercase tracking-wide text-white/45">
        {label}
      </div>
      <div className="mt-1 text-2xl font-bold tracking-tight">{value}</div>
      {sub && <div className="mt-1 text-xs">{sub}</div>}
    </motion.div>
  );
}

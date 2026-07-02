"use client";

import Link from "next/link";
import { useLive } from "@/lib/live";
import { coins, pct } from "@/lib/format";

/** Horizontal streaming price tape — the "live market" heartbeat. */
export function LiveTape() {
  const prices = useLive((s) => s.prices);
  const connected = useLive((s) => s.connected);
  const rows = Object.entries(prices).slice(0, 16);

  if (rows.length === 0) {
    return (
      <div className="glass flex items-center gap-2 px-4 py-2.5 text-xs text-white/40">
        <span className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-neon-amber" : "bg-white/30"}`} />
        {connected ? "Waiting for the first market tick…" : "Connecting to live market…"}
      </div>
    );
  }

  return (
    <div className="glass flex items-center gap-3 overflow-hidden px-3 py-2">
      <span className="flex shrink-0 items-center gap-1.5 text-xs font-semibold text-neon-green">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-neon-green" />
        LIVE
      </span>
      <div className="flex gap-4 overflow-x-auto whitespace-nowrap">
        {rows.map(([id, p]) => (
          <Link
            key={id}
            href={`/players/${id}`}
            className={`flex items-center gap-1.5 text-sm transition-colors ${
              p.flash === "up" ? "text-neon-green" : p.flash === "down" ? "text-neon-red" : "text-white/80"
            }`}
          >
            <span className="font-medium">{p.name}</span>
            <span className="tabular-nums">{coins(p.price)}</span>
            <span className={`text-xs ${p.price_change_pct >= 0 ? "text-neon-green" : "text-neon-red"}`}>
              {pct(p.price_change_pct)}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}

"use client";

import { useQuery } from "@tanstack/react-query";
import { Boxes, Clock } from "lucide-react";
import { api } from "@/lib/api";
import { coins, scoreColor, timeUntil } from "@/lib/format";
import type { SBC } from "@/lib/types";

export default function SBCPage() {
  const { data, isLoading } = useQuery({ queryKey: ["sbcs"], queryFn: api.sbcs });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">SBC Centre</h1>
        <p className="text-sm text-white/50">
          Every challenge with cost, pack value and a &ldquo;should I complete?&rdquo; verdict.
        </p>
      </header>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="glass h-40 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {data?.map((sbc) => <SBCCard key={sbc.id} sbc={sbc} />)}
        </div>
      )}
    </div>
  );
}

function SBCCard({ sbc }: { sbc: SBC }) {
  const profit = sbc.pack_value - sbc.estimated_cost;
  const worth = sbc.value_rating >= 70;
  return (
    <div className="glass glass-hover p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient shadow-glow">
            <Boxes className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="font-semibold">{sbc.name}</div>
            <div className="text-xs text-white/45">{sbc.category} · {sbc.difficulty}</div>
          </div>
        </div>
        <span className={`text-lg font-bold ${scoreColor(sbc.value_rating)}`}>
          {sbc.value_rating}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
        <Cell label="Cost" value={coins(sbc.estimated_cost)} />
        <Cell label="Pack Value" value={sbc.pack_value ? coins(sbc.pack_value) : "—"} />
        <Cell
          label="Net"
          value={sbc.pack_value ? `${profit >= 0 ? "+" : ""}${coins(profit)}` : "Reward"}
          tone={sbc.pack_value ? (profit >= 0 ? "green" : "red") : "neutral"}
        />
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className="inline-flex items-center gap-1 text-xs text-white/50">
          <Clock className="h-3.5 w-3.5" /> {timeUntil(sbc.expires_at)}
          {sbc.repeatable && <span className="chip ml-1">Repeatable</span>}
        </span>
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            worth ? "bg-neon-green/15 text-neon-green" : "bg-neon-amber/15 text-neon-amber"
          }`}
        >
          {worth ? "Worth completing" : "Situational"}
        </span>
      </div>
      <div className="mt-3 text-xs text-white/50">Reward: {sbc.reward}</div>
    </div>
  );
}

function Cell({ label, value, tone = "neutral" }: { label: string; value: string; tone?: string }) {
  const color = { green: "text-neon-green", red: "text-neon-red", neutral: "text-white" }[tone] ?? "text-white";
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-2.5">
      <div className="text-[11px] text-white/45">{label}</div>
      <div className={`text-sm font-bold ${color}`}>{value}</div>
    </div>
  );
}

"use client";

import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import { PlayerRow } from "@/components/ui";

const LEAGUES = [
  "All",
  "Premier League",
  "LALIGA EA SPORTS",
  "Bundesliga",
  "Serie A",
  "Ligue 1",
  "Icons",
];

export default function MarketPage() {
  const [q, setQ] = useState("");
  const [league, setLeague] = useState("All");
  const [minRating, setMinRating] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ["players", q, league, minRating],
    queryFn: () =>
      api.players({
        q: q || undefined,
        league: league === "All" ? undefined : league,
        min_rating: minRating || undefined,
      }),
  });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Live Market</h1>
        <p className="text-sm text-white/50">
          Search every card. Tap any player for AI intelligence and live graphs.
        </p>
      </header>

      <div className="glass p-4">
        <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-black/20 px-3 py-2.5">
          <Search className="h-4 w-4 text-white/40" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search players… (e.g. Mbappé, Saka, Zidane)"
            className="w-full bg-transparent text-sm outline-none placeholder:text-white/30"
          />
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          {LEAGUES.map((l) => (
            <button
              key={l}
              onClick={() => setLeague(l)}
              className={`chip glass-hover ${
                league === l ? "border-brand-violet/50 bg-brand-violet/15 text-white" : "text-white/60"
              }`}
            >
              {l}
            </button>
          ))}
          <div className="ml-auto flex items-center gap-2 text-xs text-white/50">
            <span>Min rating {minRating || "any"}</span>
            <input
              type="range"
              min={0}
              max={95}
              step={1}
              value={minRating}
              onChange={(e) => setMinRating(Number(e.target.value))}
              className="accent-brand-violet"
            />
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="glass h-[68px] animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data?.map((p) => (
            <PlayerRow key={p.id} player={p} />
          ))}
        </div>
      )}
      {data?.length === 0 && (
        <p className="py-10 text-center text-sm text-white/40">No players match those filters.</p>
      )}
    </div>
  );
}

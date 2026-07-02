"use client";

import { useQuery } from "@tanstack/react-query";
import { Shield, Star } from "lucide-react";
import { useMemo } from "react";
import { api } from "@/lib/api";
import { RatingBadge, StatCard } from "@/components/ui";
import { coins } from "@/lib/format";
import type { ClubPlayer } from "@/lib/types";

export default function ClubPage() {
  const { data, isLoading } = useQuery({ queryKey: ["club"], queryFn: api.club });

  const stats = useMemo(() => {
    const rows = data ?? [];
    const totalCards = rows.reduce((n, p) => n + p.quantity, 0);
    const clubValue = rows.reduce((n, p) => n + p.market_value * p.quantity, 0);
    const dupes = rows.filter((p) => p.quantity > 1).length;
    const fodderValue = rows
      .filter((p) => p.rating <= 84 && !p.is_favourite)
      .reduce((n, p) => n + p.market_value * p.quantity, 0);
    return { totalCards, clubValue, dupes, fodderValue };
  }, [data]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">My Club</h1>
        <p className="text-sm text-white/50">
          Your fodder and cards — the raw material the AI SBC Solver draws from.
        </p>
      </header>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total Cards" value={`${stats.totalCards}`} accent="purple" />
        <StatCard label="Club Value" value={coins(stats.clubValue)} accent="blue" />
        <StatCard label="Fodder Value" value={coins(stats.fodderValue)} accent="green" />
        <StatCard label="Duplicates" value={`${stats.dupes}`} accent="purple" />
      </div>

      {isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="glass h-[68px] animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data?.map((p) => <ClubCard key={p.player_id} player={p} />)}
        </div>
      )}
    </div>
  );
}

function ClubCard({ player }: { player: ClubPlayer }) {
  return (
    <div className="glass flex items-center gap-3 p-3">
      <RatingBadge
        player={{
          id: player.player_id,
          name: player.name,
          rating: player.rating,
          position: player.position,
          club: player.club,
          league: player.league,
          nation: player.nation,
          card_type: player.card_type,
          image_url: null,
          price: player.market_value,
          price_change_pct: 0,
        }}
      />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className="truncate text-sm font-semibold">{player.name}</span>
          {player.is_favourite && <Star className="h-3 w-3 shrink-0 fill-neon-amber text-neon-amber" />}
          {player.untradeable && <Shield className="h-3 w-3 shrink-0 text-white/30" />}
        </div>
        <div className="truncate text-xs text-white/45">{player.league}</div>
      </div>
      <div className="text-right">
        <div className="text-sm font-semibold">{coins(player.market_value)}</div>
        {player.quantity > 1 && <div className="text-[11px] text-brand-violet">×{player.quantity}</div>}
      </div>
    </div>
  );
}

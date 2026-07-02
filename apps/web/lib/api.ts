import type {
  Dashboard,
  PlayerDetail,
  PlayerSummary,
  SBC,
  Scanner,
} from "./types";

const BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    // Prices move constantly — always fetch fresh, let React Query cache.
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  dashboard: () => get<Dashboard>("/dashboard"),
  scanner: (limit = 8) => get<Scanner>(`/market/scanner?limit=${limit}`),
  players: (params: { q?: string; league?: string; min_rating?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.q) qs.set("q", params.q);
    if (params.league) qs.set("league", params.league);
    if (params.min_rating) qs.set("min_rating", String(params.min_rating));
    const s = qs.toString();
    return get<PlayerSummary[]>(`/players${s ? `?${s}` : ""}`);
  },
  player: (id: number | string) => get<PlayerDetail>(`/players/${id}`),
  sbcs: () => get<SBC[]>("/sbcs"),
};

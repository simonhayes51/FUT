import { create } from "zustand";

export interface LivePrice {
  price: number;
  price_change_pct: number;
  name: string;
  rating: number;
  flash: "up" | "down" | null;
}

export interface LiveAlert {
  name: string;
  price: number;
  target: number;
  direction: string;
}

interface LiveState {
  connected: boolean;
  prices: Record<number, LivePrice>;
  alerts: LiveAlert[];
  setConnected: (v: boolean) => void;
  applyTick: (prices: TickPrice[], alerts: LiveAlert[]) => void;
}

interface TickPrice {
  player_id: number;
  name: string;
  rating: number;
  price: number;
  price_change_pct: number;
}

export const useLive = create<LiveState>((set) => ({
  connected: false,
  prices: {},
  alerts: [],
  setConnected: (v) => set({ connected: v }),
  applyTick: (incoming, alerts) =>
    set((state) => {
      const prices = { ...state.prices };
      for (const p of incoming) {
        const prev = prices[p.player_id]?.price;
        prices[p.player_id] = {
          price: p.price,
          price_change_pct: p.price_change_pct,
          name: p.name,
          rating: p.rating,
          flash: prev === undefined ? null : p.price > prev ? "up" : p.price < prev ? "down" : null,
        };
      }
      return {
        prices,
        alerts: alerts.length ? [...alerts, ...state.alerts].slice(0, 8) : state.alerts,
      };
    }),
}));

/** Derive the WS URL from the REST base (http→ws, /api/v1 → /api/v1/ws/market). */
export function marketSocketUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  return base.replace(/^http/, "ws") + "/ws/market";
}

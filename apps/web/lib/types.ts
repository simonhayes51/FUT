// Mirrors the FastAPI response contract (apps/api/app/schemas.py).

export interface PlayerSummary {
  id: number;
  name: string;
  rating: number;
  position: string;
  club: string;
  league: string;
  nation: string;
  card_type: string;
  image_url: string | null;
  price: number;
  price_change_pct: number;
}

export interface AIRating {
  score: number;
  confidence: number;
  verdict: "BUY" | "HOLD" | "SELL" | "AVOID";
  risk: "Low" | "Medium" | "High";
  time_horizon: string;
  expected_roi_pct: number;
  suggested_buy: number;
  suggested_sell: number;
  expected_peak: number;
  reasons: string[];
}

export interface Analytics {
  lowest_bin: number;
  highest_bin: number;
  volume: number;
  supply: number;
  demand: number;
  volatility: number;
  buy_score: number;
  sell_score: number;
  hold_score: number;
}

export interface PricePoint {
  price: number;
  recorded_at: string;
}

export interface PlayerDetail extends PlayerSummary {
  analytics: Analytics | null;
  ai: AIRating | null;
  history: PricePoint[];
}

export interface ScannerRow {
  player: PlayerSummary;
  metric: number;
  label: string;
}

export interface Dashboard {
  club_value: number;
  coin_balance: number;
  transfer_profit: number;
  profit_this_week: number;
  profit_this_month: number;
  open_positions: number;
  watchlist_count: number;
  active_alerts: number;
  trending: PlayerSummary[];
  top_investments: ScannerRow[];
  assistant_briefing: string[];
}

export type Scanner = Record<string, ScannerRow[]>;

export interface SBC {
  id: number;
  name: string;
  category: string;
  expires_at: string | null;
  reward: string;
  estimated_cost: number;
  pack_value: number;
  value_rating: number;
  difficulty: string;
  repeatable: boolean;
}

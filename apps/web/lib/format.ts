// Display helpers shared across the UI.

export function coins(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return `${Math.round(n)}`;
}

export function coinsFull(n: number): string {
  return n.toLocaleString("en-GB");
}

export function pct(n: number): string {
  return `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;
}

export function verdictColor(v: string): string {
  switch (v) {
    case "BUY":
      return "text-neon-green";
    case "SELL":
      return "text-neon-red";
    case "AVOID":
      return "text-neon-red";
    default:
      return "text-neon-amber";
  }
}

export function scoreColor(score: number): string {
  if (score >= 75) return "text-neon-green";
  if (score >= 55) return "text-neon-amber";
  return "text-neon-red";
}

export function timeUntil(iso: string | null): string {
  if (!iso) return "No expiry";
  const ms = new Date(iso).getTime() - Date.now();
  if (ms <= 0) return "Expired";
  const days = Math.floor(ms / 86_400_000);
  const hours = Math.floor((ms % 86_400_000) / 3_600_000);
  if (days > 0) return `${days}d ${hours}h left`;
  return `${hours}h left`;
}

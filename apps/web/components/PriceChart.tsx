"use client";

import { useMemo, useState } from "react";
import type { PricePoint } from "@/lib/types";
import { coins } from "@/lib/format";

// Dependency-free SVG area chart. Keeps the bundle lean and renders identically
// on server and client (no layout measurement needed thanks to viewBox).
export function PriceChart({
  data,
  height = 220,
}: {
  data: PricePoint[];
  height?: number;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const W = 720;
  const H = height;
  const pad = 8;

  const { path, area, points, min, max } = useMemo(() => {
    const prices = data.map((d) => d.price);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = max - min || 1;
    const step = data.length > 1 ? (W - pad * 2) / (data.length - 1) : 0;

    const points = data.map((d, i) => {
      const x = pad + i * step;
      const y = pad + (1 - (d.price - min) / range) * (H - pad * 2);
      return { x, y, price: d.price, at: d.recorded_at };
    });

    const path = points
      .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`)
      .join(" ");
    const area = `${path} L${points[points.length - 1]?.x ?? 0},${H - pad} L${
      points[0]?.x ?? 0
    },${H - pad} Z`;

    return { path, area, points, min, max };
  }, [data, H]);

  if (data.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-white/40">
        No price history
      </div>
    );
  }

  const rising = data[data.length - 1].price >= data[0].price;
  const stroke = rising ? "#34d399" : "#fb7185";
  const active = hover !== null ? points[hover] : null;

  return (
    <div className="relative w-full">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        preserveAspectRatio="none"
        onMouseLeave={() => setHover(null)}
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const rel = ((e.clientX - rect.left) / rect.width) * W;
          const idx = Math.round(((rel - pad) / (W - pad * 2)) * (data.length - 1));
          setHover(Math.max(0, Math.min(data.length - 1, idx)));
        }}
      >
        <defs>
          <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={stroke} stopOpacity="0.28" />
            <stop offset="100%" stopColor={stroke} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={area} fill="url(#fill)" />
        <path d={path} fill="none" stroke={stroke} strokeWidth="2" vectorEffect="non-scaling-stroke" />
        {active && (
          <>
            <line
              x1={active.x}
              y1={pad}
              x2={active.x}
              y2={H - pad}
              stroke="rgba(255,255,255,0.25)"
              strokeWidth="1"
              vectorEffect="non-scaling-stroke"
            />
            <circle cx={active.x} cy={active.y} r="4" fill={stroke} stroke="#0a0a12" strokeWidth="2" />
          </>
        )}
      </svg>

      <div className="pointer-events-none absolute right-2 top-1 text-[11px] text-white/40">
        H {coins(max)} · L {coins(min)}
      </div>

      {active && (
        <div className="pointer-events-none absolute left-2 top-1 rounded-lg border border-white/10 bg-base-900/90 px-2.5 py-1.5 text-xs backdrop-blur">
          <div className="font-semibold">{coins(active.price)} coins</div>
          <div className="text-white/40">
            {new Date(active.at).toLocaleString("en-GB", {
              day: "2-digit",
              month: "short",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>
        </div>
      )}
    </div>
  );
}

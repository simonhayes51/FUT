"use client";

import {
  Bell,
  Boxes,
  BrainCircuit,
  LayoutDashboard,
  LineChart,
  Shield,
  Sparkles,
  Trophy,
  Wallet,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/market", label: "Live Market", icon: LineChart },
  { href: "/sbc", label: "SBC Solver", icon: Boxes },
  { href: "/club", label: "My Club", icon: Shield },
  { href: "/coach", label: "AI Coach", icon: BrainCircuit },
  { href: "/portfolio", label: "Portfolio", icon: Wallet, soon: true },
  { href: "/squad", label: "Squad Builder", icon: Trophy, soon: true },
  { href: "/alerts", label: "Alerts", icon: Bell, soon: true },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col gap-1 border-r border-white/10 p-4 md:flex">
      <div className="mb-6 flex items-center gap-2.5 px-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-gradient shadow-glow">
          <Sparkles className="h-5 w-5 text-white" />
        </div>
        <div>
          <div className="text-lg font-bold leading-none tracking-tight">
            FC <span className="gradient-text">Edge</span>
          </div>
          <div className="text-[10px] uppercase tracking-widest text-white/40">
            Trading Terminal
          </div>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV.map(({ href, label, icon: Icon, soon }) => {
          const active =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={soon ? "#" : href}
              className={`group flex items-center justify-between rounded-xl px-3 py-2.5 text-sm font-medium transition-all ${
                active
                  ? "bg-white/10 text-white shadow-glow"
                  : "text-white/55 hover:bg-white/5 hover:text-white"
              }`}
            >
              <span className="flex items-center gap-3">
                <Icon className="h-[18px] w-[18px]" />
                {label}
              </span>
              {soon && (
                <span className="rounded-full bg-white/5 px-1.5 py-0.5 text-[9px] uppercase text-white/40">
                  soon
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto glass p-3">
        <div className="flex items-center gap-1.5 text-xs font-semibold">
          <Sparkles className="h-3.5 w-3.5 text-brand-violet" />
          Premium
        </div>
        <p className="mt-1 text-[11px] leading-snug text-white/50">
          Unlimited AI ratings, alerts &amp; SBC solves for £2.99/mo.
        </p>
        <button className="mt-2 w-full rounded-lg bg-brand-gradient py-1.5 text-xs font-semibold text-white transition hover:opacity-90">
          Upgrade
        </button>
      </div>
    </aside>
  );
}

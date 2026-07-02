"use client";

import { useEffect } from "react";
import { marketSocketUrl, useLive } from "@/lib/live";

/** Opens the market WebSocket once and streams ticks into the live store. */
export function LiveProvider() {
  const setConnected = useLive((s) => s.setConnected);
  const applyTick = useLive((s) => s.applyTick);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout> | null = null;
    let closed = false;

    const connect = () => {
      try {
        ws = new WebSocket(marketSocketUrl());
      } catch {
        retry = setTimeout(connect, 3000);
        return;
      }
      ws.onopen = () => setConnected(true);
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === "tick") applyTick(msg.prices ?? [], msg.alerts ?? []);
        } catch {
          /* ignore malformed frames */
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (!closed) retry = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws?.close();
    };

    connect();
    return () => {
      closed = true;
      if (retry) clearTimeout(retry);
      ws?.close();
    };
  }, [setConnected, applyTick]);

  return null;
}

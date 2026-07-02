"use client";

import { useMutation } from "@tanstack/react-query";
import { BrainCircuit, Send, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

interface Msg {
  role: "user" | "coach";
  text: string;
  engine?: string;
}

const STARTERS = [
  "What should I invest in?",
  "Which SBC is worth doing?",
  "How do I make 500k?",
  "Who should I sell?",
];

export default function CoachPage() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "coach",
      text:
        "I'm your AI Coach. I read the live market and your club to answer things like " +
        "what to buy, what to sell, which SBC to complete, or how to hit a coin target. Ask me anything.",
    },
  ]);
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  const ask = useMutation({
    mutationFn: (q: string) => api.coach(q),
    onSuccess: (res) =>
      setMessages((m) => [...m, { role: "coach", text: res.answer, engine: res.engine }]),
  });

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, ask.isPending]);

  const send = (q: string) => {
    const question = q.trim();
    if (!question || ask.isPending) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    ask.mutate(question);
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-3rem)] max-w-3xl flex-col">
      <header className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient shadow-glow">
          <BrainCircuit className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight">AI Coach</h1>
          <p className="text-xs text-white/50">Grounded in live market &amp; your club</p>
        </div>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto pr-1">
        {messages.map((m, i) => (
          <Bubble key={i} msg={m} />
        ))}
        {ask.isPending && (
          <div className="flex items-center gap-2 text-sm text-white/40">
            <Sparkles className="h-4 w-4 animate-pulse text-brand-violet" /> Reading the market…
          </div>
        )}
        <div ref={endRef} />
      </div>

      {messages.length <= 1 && (
        <div className="mb-3 mt-2 flex flex-wrap gap-2">
          {STARTERS.map((s) => (
            <button key={s} onClick={() => send(s)} className="chip glass-hover text-white/70">
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="mt-3 flex items-center gap-2 rounded-2xl border border-white/10 bg-black/30 p-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(input)}
          placeholder="Ask the coach…"
          className="w-full bg-transparent px-2 text-sm outline-none placeholder:text-white/30"
        />
        <button
          onClick={() => send(input)}
          disabled={ask.isPending}
          className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-gradient text-white transition hover:opacity-90 disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

function Bubble({ msg }: { msg: Msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-brand-gradient text-white"
            : "glass text-white/85"
        }`}
      >
        {renderMarkdown(msg.text)}
        {msg.engine === "heuristic" && !isUser && (
          <div className="mt-2 text-[10px] uppercase tracking-wide text-white/30">
            Offline engine · set OPENAI_API_KEY for LLM answers
          </div>
        )}
      </div>
    </div>
  );
}

// Minimal **bold** renderer — the coach only emits bold + line breaks.
function renderMarkdown(text: string) {
  return text.split("\n").map((line, i) => (
    <span key={i} className="block">
      {line.split(/(\*\*[^*]+\*\*)/g).map((part, j) =>
        part.startsWith("**") && part.endsWith("**") ? (
          <strong key={j} className="font-semibold text-white">
            {part.slice(2, -2)}
          </strong>
        ) : (
          <span key={j}>{part}</span>
        ),
      )}
    </span>
  ));
}

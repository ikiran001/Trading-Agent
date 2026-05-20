"use client";

import { useEffect, useState } from "react";
import { ConfidenceMeter } from "@/components/ConfidenceMeter";
import { SignalFeed } from "@/components/SignalFeed";
import { TradingViewChart } from "@/components/TradingViewChart";
import { fetchSentiment, fetchSignals } from "@/lib/api";
import { useTradingStream } from "@/lib/ws-client";

export default function Dashboard() {
  const { signals: liveSignals, connected } = useTradingStream();
  const [restSignals, setRestSignals] = useState<Record<string, unknown>[]>([]);
  const [sentiment, setSentiment] = useState({ score: 50 });

  useEffect(() => {
    fetchSignals().then(setRestSignals).catch(() => {});
    fetchSentiment().then(setSentiment).catch(() => {});
    const t = setInterval(() => {
      fetchSentiment().then(setSentiment).catch(() => {});
    }, 30000);
    return () => clearInterval(t);
  }, []);

  const signals = liveSignals.length ? liveSignals : restSignals;
  const avgConfidence =
    signals.length > 0
      ? (signals as { confidence?: number }[]).reduce((a, s) => a + (s.confidence || 0), 0) / signals.length
      : sentiment.score;

  return (
    <main className="min-h-screen p-4 md:p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold">NIFTY 50 Trading Desk</h1>
          <p className="text-gray-500 text-sm">NSE:NIFTY index & options — live intraday signals</p>
        </div>
        <span className={`text-xs px-2 py-1 rounded ${connected ? "bg-accent/20 text-accent" : "bg-danger/20 text-danger"}`}>
          {connected ? "Live" : "Reconnecting…"}
        </span>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <section className="lg:col-span-2 bg-panel rounded-xl p-4 border border-gray-800">
          <h2 className="text-sm font-medium text-gray-400 mb-2">Live chart</h2>
          <TradingViewChart symbol="NSE:NIFTY" />
        </section>

        <section className="bg-panel rounded-xl p-4 border border-gray-800 space-y-4">
          <ConfidenceMeter value={avgConfidence} />
          <div>
            <h2 className="text-sm font-medium text-gray-400 mb-2">Signals</h2>
            <SignalFeed signals={signals as Parameters<typeof SignalFeed>[0]["signals"]} />
          </div>
        </section>
      </div>

      <footer className="mt-6 text-xs text-gray-600 text-center">
        Not investment advice. Paper mode recommended until validated.
      </footer>
    </main>
  );
}

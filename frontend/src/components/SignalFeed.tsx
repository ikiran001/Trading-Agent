"use client";

type Signal = {
  signal?: string;
  symbol?: string;
  confidence?: number;
  entry?: number;
  stop_loss?: number;
  target_1?: number;
  reasons?: string[];
  market_condition?: string;
};

export function SignalFeed({ signals }: { signals: Signal[] }) {
  if (!signals.length) {
    return <p className="text-gray-500 text-sm">Waiting for live signals…</p>;
  }
  return (
    <div className="space-y-3 max-h-96 overflow-y-auto">
      {signals.map((s, i) => (
        <div key={i} className="bg-panel rounded-lg p-3 border border-gray-800">
          <div className="flex justify-between items-center">
            <span className={`font-bold ${s.signal === "BUY" ? "text-accent" : s.signal === "SELL" ? "text-danger" : "text-gray-400"}`}>
              {s.signal} {s.symbol}
            </span>
            <span className="text-sm text-gray-400">{s.confidence}%</span>
          </div>
          {s.entry != null && (
            <p className="text-xs mt-1 text-gray-400">
              Entry {s.entry} · SL {s.stop_loss} · T1 {s.target_1}
            </p>
          )}
          {s.reasons?.length ? (
            <ul className="text-xs mt-2 text-gray-500 list-disc pl-4">
              {s.reasons.slice(0, 4).map((r, j) => (
                <li key={j}>{r}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ))}
    </div>
  );
}

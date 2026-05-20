"use client";

import { useEffect, useRef } from "react";

type TradingViewWidget = (opts: Record<string, unknown>) => void;

declare global {
  interface Window {
    TradingView?: { widget: TradingViewWidget };
  }
}

export function TradingViewChart({ symbol = "NSE:NIFTY" }: { symbol?: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/tv.js";
    script.async = true;
    script.onload = () => {
      if (ref.current && window.TradingView) {
        window.TradingView.widget({
          autosize: true,
          symbol,
          interval: "5",
          timezone: "Asia/Kolkata",
          theme: "dark",
          style: "1",
          locale: "en",
          container_id: ref.current.id,
        });
      }
    };
    document.body.appendChild(script);
    return () => script.remove();
  }, [symbol]);

  return <div id="tradingview_chart" ref={ref} className="h-80 w-full rounded-lg overflow-hidden" />;
}

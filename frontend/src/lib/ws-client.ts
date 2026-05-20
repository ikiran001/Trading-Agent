"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type StreamMessage = {
  type: string;
  channel?: string;
  payload: Record<string, unknown>;
};

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/v1/stream";

export function useTradingStream() {
  const [messages, setMessages] = useState<StreamMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      setTimeout(connect, 3000);
    };
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as StreamMessage;
        setMessages((prev) => [msg, ...prev].slice(0, 100));
      } catch {
        /* ignore */
      }
    };
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const signals = messages.filter((m) => m.type === "signal").map((m) => m.payload);

  return { messages, signals, connected };
}

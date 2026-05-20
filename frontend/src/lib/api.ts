const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchSignals(active = false) {
  const res = await fetch(`${API_URL}/api/v1/signals?active=${active}&limit=30`, { cache: "no-store" });
  return res.json();
}

export async function fetchMarket(symbol: string) {
  const res = await fetch(`${API_URL}/api/v1/market/${symbol}`, { cache: "no-store" });
  return res.json();
}

export async function fetchSentiment() {
  const res = await fetch(`${API_URL}/api/v1/sentiment`, { cache: "no-store" });
  return res.json();
}

export async function fetchSectors() {
  const res = await fetch(`${API_URL}/api/v1/sectors`, { cache: "no-store" });
  return res.json();
}

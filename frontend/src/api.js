const BASE = ""; // same origin via Vite proxy

async function get(path) {
  const res = await fetch(BASE + path);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  dashboard: () => get("/api/dashboard"),
  regionRisk: (id) => get(`/regions/${id}/risk`),
  recommendations: (id) => get(`/regions/${id}/recommendations`),
  riskTrend: (id, hours = 24) =>
    get(`/regions/${id}/risk/trend?hours=${hours}`),
  safeRoute: (origin, dest) =>
    fetch("/routes/safe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ origin, destination: dest }),
    }).then((r) => r.json()),
};

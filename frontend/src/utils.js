export const RISK_COLORS = {
  RENDAH: "#2dc653",
  SEDANG: "#f4a621",
  TINGGI: "#f25c54",
  KRITIS: "#b44fd4",
};

export function getRiskColor(category) {
  return RISK_COLORS[category] || RISK_COLORS.RENDAH;
}

export function getRiskBadgeClass(category) {
  return `badge-${(category || "rendah").toLowerCase()}`;
}

export function formatURS(val) {
  return typeof val === "number" ? val.toFixed(1) : "-";
}

export function filterRegions(regions, cityFilter, search) {
  let list = [...regions];
  if (cityFilter && cityFilter !== "Semua") {
    list = list.filter(
      (r) =>
        (r.kota || "").toLowerCase().includes(cityFilter.toLowerCase()) ||
        (r.region_name || "").toLowerCase().includes(cityFilter.toLowerCase()),
    );
  }
  if (search) {
    const q = search.toLowerCase();
    list = list.filter(
      (r) =>
        (r.region_name || "").toLowerCase().includes(q) ||
        (r.kota || "").toLowerCase().includes(q),
    );
  }
  return list.sort((a, b) => b.urban_risk_score - a.urban_risk_score);
}

export const CITIES = [
  "Semua",
  "Jakarta",
  "Bandung",
  "Bogor",
  "Bekasi",
  "Depok",
];

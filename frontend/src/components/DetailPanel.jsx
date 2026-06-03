import { useQuery } from "@tanstack/react-query";
import { useStore } from "../store";
import { api } from "../api";
import { getRiskColor, getRiskBadgeClass, formatURS } from "../utils";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Ikon per tipe rekomendasi — pakai gambar custom
const TYPE_ICON = {
  alert: { img: "/allert.png", label: "Peringatan" },
  route: { img: "/rute.png", label: "Rute" },
  service: { img: "/fasilitas.png", label: "Fasilitas" },
  evacuation: { img: "/allert.png", label: "Evakuasi" },
  resource_allocation: { img: "/fasilitas.png", label: "Sumber Daya" },
};

function UrgencyBadge({ urgency }) {
  const u = (urgency || "").toLowerCase();
  const styles = {
    segera: "bg-[#b44fd4]/20 text-[#b44fd4] border border-[#b44fd4]/30",
    waspada: "bg-[#f25c54]/20 text-[#f25c54] border border-[#f25c54]/30",
    siaga: "bg-[#f4a621]/20 text-[#f4a621] border border-[#f4a621]/30",
  };
  return (
    <span
      className={`inline-flex items-center text-[8px] font-bold px-1.5 py-0.5
                      rounded uppercase tracking-wide ${styles[u] || styles.siaga}`}
    >
      {urgency}
    </span>
  );
}

function RecCard({ rec }) {
  const typeInfo = TYPE_ICON[rec.type] || {
    img: "/allert.png",
    label: rec.type || "Info",
  };
  return (
    <div
      className="card px-3 py-2.5 mb-2 border-l-2"
      style={{
        borderLeftColor:
          rec.urgency?.toLowerCase() === "segera"
            ? "#b44fd4"
            : rec.urgency?.toLowerCase() === "waspada"
              ? "#f25c54"
              : "#f4a621",
      }}
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-1.5 min-w-0">
          <img
            src={typeInfo.img}
            alt={typeInfo.label}
            className="w-5 h-5 object-contain flex-shrink-0"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
          <span className="text-[10px] font-semibold text-t2 flex-shrink-0">
            {typeInfo.label}
          </span>
        </div>
        <UrgencyBadge urgency={rec.urgency} />
      </div>
      <p className="text-[10.5px] text-t1 leading-relaxed pl-6">
        {rec.description}
      </p>
    </div>
  );
}

function StatBar({ label, value, color, max = 100 }) {
  const pct = Math.max(2, Math.round((parseFloat(value) / max) * 100));
  return (
    <div className="card px-3 py-2.5">
      <p className="text-[8.5px] text-t3 uppercase tracking-[0.5px] font-semibold mb-1.5">
        {label}
      </p>
      <div className="flex items-center gap-2">
        <span
          className="font-mono text-[15px] font-bold flex-shrink-0"
          style={{ color }}
        >
          {value}
        </span>
        <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{ width: `${pct}%`, background: color }}
          />
        </div>
      </div>
    </div>
  );
}

function TrendChart({ regionId }) {
  const { data } = useQuery({
    queryKey: ["trend", regionId],
    queryFn: () => api.riskTrend(regionId, 24),
    enabled: !!regionId,
  });
  const points = data?.trend ?? [];
  if (!points.length) return null;

  return (
    <div className="card p-3">
      <p className="text-[9px] text-t3 uppercase tracking-[0.6px] font-semibold mb-2">
        Tren URS (24 jam)
      </p>
      <ResponsiveContainer width="100%" height={60}>
        <AreaChart
          data={points}
          margin={{ top: 2, right: 4, bottom: 0, left: -24 }}
        >
          <defs>
            <linearGradient id="ursGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00b4d8" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#00b4d8" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="date" hide />
          <YAxis domain={[0, 100]} tick={{ fontSize: 8, fill: "#3a6a8c" }} />
          <Tooltip
            contentStyle={{
              background: "#0f2040",
              border: "1px solid #1a3a5c",
              fontSize: 10,
            }}
            labelFormatter={() => ""}
            formatter={(v) => [v.toFixed(1), "URS"]}
          />
          <Area
            type="monotone"
            dataKey="urban_risk_score"
            stroke="#00b4d8"
            strokeWidth={1.5}
            fill="url(#ursGrad)"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function SkeletonDetail() {
  return (
    <div className="p-4 flex flex-col gap-3">
      <div className="skeleton h-4 w-36 mb-1" />
      <div className="skeleton h-3 w-24" />
      <div className="card p-4">
        <div className="skeleton h-10 w-16 mx-auto mb-2" />
        <div className="skeleton h-2 w-full rounded-full mt-2" />
      </div>
      <div className="grid grid-cols-3 gap-2">
        {[0, 1, 2].map((i) => (
          <div key={i} className="card p-3">
            <div className="skeleton h-3 w-14 mb-2" />
            <div className="skeleton h-4 w-10" />
          </div>
        ))}
      </div>
      <div className="skeleton h-16 rounded-lg" />
      <div className="skeleton h-14 rounded-lg" />
      <div className="skeleton h-14 rounded-lg" />
    </div>
  );
}

export default function DetailPanel({ regions, fullscreen = false }) {
  const { selectedRegionId, clearSelectedRegion } = useStore();
  const region = regions.find((r) => r.region_id === selectedRegionId);

  const { data: recData, isLoading } = useQuery({
    queryKey: ["recs", selectedRegionId],
    queryFn: () => api.recommendations(selectedRegionId),
    enabled: !!selectedRegionId,
  });

  if (!selectedRegionId) return null;

  const color = getRiskColor(region?.risk_category);
  const recs = recData?.recommendations ?? [];
  const urs = Math.round(region?.urban_risk_score ?? 0);
  const ursPct = Math.max(2, urs);

  return (
    <div
      className={`flex flex-col bg-b1 overflow-hidden
                     ${
                       fullscreen
                         ? "h-full w-full"
                         : "border-l border-bd w-[320px] flex-shrink-0"
                     }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-bd flex-shrink-0">
        <div className="min-w-0">
          <h3 className="text-[13px] font-extrabold text-t1 truncate">
            {region?.region_name ?? "—"}
          </h3>
          <p className="text-[10px] text-t3">{region?.kota ?? ""}</p>
        </div>
        <button
          onClick={clearSelectedRegion}
          className="flex-shrink-0 ml-2 text-t3 hover:text-t1 text-xs border border-bd
                     hover:border-t2 rounded px-2 py-1 transition-colors"
        >
          ✕ Tutup
        </button>
      </div>

      {/* Scrollable */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {isLoading && !region ? (
          <SkeletonDetail />
        ) : (
          <div className="p-4 flex flex-col gap-3">
            {/* URS — gauge dengan progress bar */}
            <div className="card p-4">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="text-[9px] text-t3 uppercase tracking-[0.6px] font-semibold">
                    Urban Risk Score
                  </p>
                  <span
                    className={`risk-badge mt-0.5 ${getRiskBadgeClass(region?.risk_category)}`}
                  >
                    {region?.risk_category}
                  </span>
                </div>
                <p
                  className="font-mono text-[42px] font-extrabold leading-none"
                  style={{ color }}
                >
                  {urs}
                </p>
              </div>
              {/* Progress bar */}
              <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${ursPct}%`, background: color }}
                />
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-[8px] text-t3">0</span>
                <span className="text-[8px] text-t3">100</span>
              </div>
            </div>

            {/* 3 stat bars */}
            <div className="grid grid-cols-1 gap-2">
              <StatBar
                label="Risiko Banjir"
                value={formatURS(region?.flood_risk)}
                color="#f25c54"
              />
              <StatBar
                label="Dampak Lalu Lintas"
                value={formatURS(region?.traffic_impact)}
                color="#f4a621"
              />
              <StatBar
                label="Aksesibilitas"
                value={formatURS(region?.service_access)}
                color="#2dc653"
              />
            </div>

            {/* Trend */}
            <TrendChart regionId={selectedRegionId} />

            {/* Rekomendasi */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-[9px] text-t3 uppercase tracking-[0.6px] font-semibold">
                  Rekomendasi Tindakan
                </p>
                {recs.length > 0 && (
                  <span
                    className="text-[8px] text-t3 bg-b2 border border-bd
                                   px-1.5 py-0.5 rounded font-mono"
                  >
                    {recs.length} item
                  </span>
                )}
              </div>

              {isLoading ? (
                <>
                  <div className="skeleton h-14 rounded-lg mb-2" />
                  <div className="skeleton h-14 rounded-lg" />
                </>
              ) : recs.length === 0 ? (
                <div className="card px-3 py-4 text-center">
                  <p className="text-xl mb-1">✅</p>
                  <p className="text-[10.5px] text-t2">
                    Tidak ada rekomendasi aktif
                  </p>
                  <p className="text-[9px] text-t3 mt-0.5">
                    Kondisi wilayah relatif aman
                  </p>
                </div>
              ) : (
                recs.slice(0, 6).map((r, i) => <RecCard key={i} rec={r} />)
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

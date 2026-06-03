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

function StatCard({ label, value, color }) {
  return (
    <div className="card px-3 py-2.5">
      <p className="text-[8.5px] text-t3 uppercase tracking-[0.5px] font-semibold mb-1">
        {label}
      </p>
      <p className="font-mono text-[16px] font-bold" style={{ color }}>
        {value ?? <span className="skeleton inline-block h-4 w-10" />}
      </p>
    </div>
  );
}

function SkeletonDetail() {
  return (
    <div className="p-4 flex flex-col gap-3">
      <div className="flex justify-between items-start">
        <div>
          <div className="skeleton h-4 w-36 mb-2" />
          <div className="skeleton h-3 w-24" />
        </div>
        <div className="skeleton h-5 w-14 rounded" />
      </div>
      <div className="card p-4 text-center">
        <div className="skeleton h-10 w-16 mx-auto mb-2" />
        <div className="skeleton h-3 w-28 mx-auto" />
      </div>
      <div className="grid grid-cols-3 gap-2">
        {[0, 1, 2].map((i) => (
          <div key={i} className="card p-3">
            <div className="skeleton h-3 w-16 mb-2" />
            <div className="skeleton h-5 w-10" />
          </div>
        ))}
      </div>
      <div className="skeleton h-24 rounded-lg" />
      <div className="skeleton h-16 rounded-lg" />
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
      <ResponsiveContainer width="100%" height={70}>
        <AreaChart
          data={points}
          margin={{ top: 2, right: 4, bottom: 0, left: -20 }}
        >
          <defs>
            <linearGradient id="ursGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00b4d8" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#00b4d8" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="date" hide />
          <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: "#3a6a8c" }} />
          <Tooltip
            contentStyle={{
              background: "#0f2040",
              border: "1px solid #1a3a5c",
              fontSize: 11,
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

export default function DetailPanel({ regions }) {
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

  return (
    <div
      className="flex flex-col bg-b1 border-l border-bd overflow-hidden w-[320px] flex-shrink-0
                    animate-in slide-in-from-right duration-200"
    >
      {/* Sticky header */}
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

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && !region ? (
          <SkeletonDetail />
        ) : (
          <div className="p-4 flex flex-col gap-3">
            {/* URS gauge */}
            <div className="card p-4 text-center">
              <p
                className="font-mono text-[40px] font-extrabold leading-none mb-1"
                style={{ color }}
              >
                {Math.round(region?.urban_risk_score ?? 0)}
              </p>
              <div className="flex items-center justify-center gap-2">
                <p className="text-[9px] text-t3 uppercase tracking-[0.6px]">
                  Urban Risk Score
                </p>
                <span
                  className={`risk-badge ${getRiskBadgeClass(region?.risk_category)}`}
                >
                  {region?.risk_category}
                </span>
              </div>
            </div>

            {/* 3 stats */}
            <div className="grid grid-cols-3 gap-2">
              <StatCard
                label="Risiko Banjir"
                value={formatURS(region?.flood_risk)}
                color="#f25c54"
              />
              <StatCard
                label="Lalu Lintas"
                value={formatURS(region?.traffic_impact)}
                color="#f4a621"
              />
              <StatCard
                label="Aksesibilitas"
                value={formatURS(region?.service_access)}
                color="#2dc653"
              />
            </div>

            {/* Trend chart */}
            <TrendChart regionId={selectedRegionId} />

            {/* Recommendations */}
            <div>
              <p className="text-[9px] text-t3 uppercase tracking-[0.6px] font-semibold mb-2">
                Rekomendasi Tindakan
              </p>
              {isLoading ? (
                <>
                  <div className="skeleton h-14 rounded-lg mb-2" />
                  <div className="skeleton h-14 rounded-lg" />
                </>
              ) : recs.length === 0 ? (
                <p className="text-[10.5px] text-t3 italic">
                  Tidak ada rekomendasi aktif.
                </p>
              ) : (
                recs.slice(0, 5).map((r, i) => (
                  <div key={i} className="card px-3 py-2.5 mb-2">
                    <span
                      className={`inline-block text-[8px] font-bold px-1.5 py-0.5 rounded uppercase
                                     tracking-wide mb-1.5
                                     ${
                                       r.urgency?.toLowerCase() === "segera"
                                         ? "bg-[#b44fd4]/20 text-[#b44fd4]"
                                         : r.urgency?.toLowerCase() ===
                                             "waspada"
                                           ? "bg-[#f25c54]/20 text-[#f25c54]"
                                           : "bg-[#f4a621]/20 text-[#f4a621]"
                                     }`}
                    >
                      {r.urgency}
                    </span>
                    <p className="text-[10.5px] text-t2 leading-relaxed">
                      {r.description}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

function KpiCard({ label, value, sub, accentClass }) {
  return (
    <div className={`card relative overflow-hidden px-4 py-3`}>
      <div
        className={`absolute top-0 left-0 right-0 h-[2.5px] rounded-t-lg ${accentClass}`}
      />
      <p className="text-[9px] text-t3 uppercase tracking-[0.7px] font-semibold mb-1">
        {label}
      </p>
      {value !== undefined ? (
        <p className="font-mono text-[18px] font-bold text-t1">{value}</p>
      ) : (
        <div className="skeleton h-5 w-16 mt-1" />
      )}
      <p className="text-[9.5px] text-t2 mt-0.5">{sub}</p>
    </div>
  );
}

export default function KpiCards() {
  const { data } = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboard,
  });
  const s = data?.summary;

  return (
    <div className="grid grid-cols-3 gap-2 px-5 py-2 bg-b0 flex-shrink-0">
      <KpiCard
        label="Wilayah Kritis"
        value={s?.kritis_count}
        sub={`dari ${s?.total_regions ?? "—"} wilayah`}
        accentClass="bg-gradient-to-r from-[#b44fd4] to-[#f25c54]"
      />
      <KpiCard
        label="Rata-rata URS"
        value={s ? s.avg_urs.toFixed(1) : undefined}
        sub="Urban Risk Score"
        accentClass="bg-gradient-to-r from-accent to-[#0096c7]"
      />
      <KpiCard
        label="Wilayah Dipantau"
        value={s?.total_regions}
        sub="Jakarta & Jawa Barat"
        accentClass="bg-gradient-to-r from-[#2dc653] to-accent"
      />
    </div>
  );
}

import { useStore } from "../store";
import {
  filterRegions,
  getRiskColor,
  getRiskBadgeClass,
  CITIES,
} from "../utils";

function RegionCard({ region, index, isSelected, onClick }) {
  const color = getRiskColor(region.risk_category);
  const pct = Math.max(4, Math.round(region.urban_risk_score));

  return (
    <div
      onClick={onClick}
      className={`card px-3 py-2.5 mb-1.5 cursor-pointer transition-all duration-150
                  hover:border-accent hover:bg-b2h hover:translate-x-0.5
                  ${isSelected ? "border-accent bg-accent/5" : ""}`}
    >
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-[9px] text-t3 flex-shrink-0">#{index + 1}</span>
          <span className="text-[11.5px] font-bold text-t1 truncate">
            {region.region_name}
          </span>
        </div>
        <span
          className={`risk-badge flex-shrink-0 ml-1 ${getRiskBadgeClass(region.risk_category)}`}
        >
          {region.risk_category}
        </span>
      </div>
      <p className="text-[9px] text-t3 mb-1.5">{region.kota}</p>
      <div className="flex items-center gap-2">
        <span
          className="font-mono text-[12px] font-bold flex-shrink-0"
          style={{ color }}
        >
          {region.urban_risk_score.toFixed(1)}
        </span>
        <div className="flex-1 h-[3px] bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${pct}%`, background: color }}
          />
        </div>
      </div>
    </div>
  );
}

// Bagian filter + search yang bisa dipakai standalone
export function SidebarFilters() {
  const { cityFilter, search, setCityFilter, setSearch } = useStore();
  return (
    <div className="px-3.5 pt-3 pb-2.5 border-b border-bd flex-shrink-0">
      <div
        className="flex gap-1 mb-2 overflow-x-auto pb-0.5
                      [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
      >
        {CITIES.map((city) => (
          <button
            key={city}
            onClick={() => setCityFilter(city)}
            className={`text-[10px] font-semibold px-2.5 py-1 rounded border
                        transition-all duration-150 flex-shrink-0
                        ${
                          cityFilter === city
                            ? "bg-accent/15 border-accent text-accent"
                            : "bg-b2 border-bd text-t3 hover:border-accent hover:text-t2"
                        }`}
          >
            {city}
          </button>
        ))}
      </div>
      <div className="relative">
        <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-t3 text-xs">
          🔍
        </span>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Cari wilayah..."
          className="w-full bg-b2 border border-bd rounded-md pl-7 pr-3 py-1.5
                     text-[11.5px] text-t1 placeholder:text-t3 outline-none
                     focus:border-accent transition-colors"
        />
      </div>
    </div>
  );
}

// Daftar region yang scrollable
export function SidebarList({ regions, onSelect }) {
  const { selectedRegionId, cityFilter, search, setSelectedRegion } =
    useStore();
  const filtered = filterRegions(regions, cityFilter, search);

  function handleSelect(id) {
    setSelectedRegion(id);
    onSelect?.();
  }

  return (
    <div className="flex-1 overflow-y-auto px-2.5 py-2 min-h-0">
      {filtered.length === 0 ? (
        <p className="text-center text-t3 text-[11px] mt-6">
          Tidak ada wilayah ditemukan
        </p>
      ) : (
        filtered.map((r, i) => (
          <RegionCard
            key={r.region_id}
            region={r}
            index={i}
            isSelected={r.region_id === selectedRegionId}
            onClick={() => handleSelect(r.region_id)}
          />
        ))
      )}
    </div>
  );
}

// Sidebar desktop — fixed width, border kiri
export default function Sidebar({ regions, onSelect }) {
  return (
    <div className="flex flex-col bg-b1 border-l border-bd overflow-hidden w-[300px] flex-shrink-0 h-full">
      <div className="px-3.5 pt-3 pb-0 flex-shrink-0">
        <p className="text-[10px] text-t2 uppercase tracking-[0.6px] font-bold mb-2">
          Daftar Wilayah
        </p>
      </div>
      <SidebarFilters />
      <SidebarList regions={regions} onSelect={onSelect} />
    </div>
  );
}

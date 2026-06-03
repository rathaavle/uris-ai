import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

export default function Header({ onMenuToggle }) {
  const { dataUpdatedAt } = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboard,
  });

  const now = new Date(dataUpdatedAt || Date.now());
  const lastTime = now.toLocaleTimeString("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
  });
  const lastDate = now.toLocaleDateString("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  return (
    <header
      className="flex items-center justify-between px-3 sm:px-5 h-[52px] sm:h-[64px]
                       flex-shrink-0 bg-gradient-to-r from-b1 to-b2 border-b border-bd z-50 overflow-hidden"
    >
      {/* Left — Logo (klik → landing page) */}
      <a href="/" className="flex items-center gap-3 group">
        <div className="flex-shrink-0 flex items-center">
          {/* Desktop — logo panjang */}
          <img
            src="/logowhite_nobg.png"
            alt="URIS-AI"
            className="hidden sm:block h-12 w-auto max-w-[160px] object-contain
                       group-hover:opacity-80 transition-opacity duration-150"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
          {/* Mobile — icon saja */}
          <img
            src="/logowhite_single.png"
            alt="URIS-AI"
            className="sm:hidden h-9 w-9 object-contain
                       group-hover:opacity-80 transition-opacity duration-150"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
        </div>
        <div className="w-px h-6 sm:h-8 bg-bd flex-shrink-0" />
        <div className="hidden sm:block">
          <p className="text-[10px] text-t3 leading-tight group-hover:text-t2 transition-colors">
            Urban Risk Intelligence System
          </p>
          <p className="text-[9px] text-t3/60 leading-tight">
            Jakarta &amp; Jawa Barat · Flood-Aware Mobility
          </p>
        </div>
        <div className="sm:hidden">
          <p className="text-[11px] font-bold text-t1 leading-tight">URIS-AI</p>
          <p className="text-[8px] text-t3 leading-tight">Urban Risk System</p>
        </div>
      </a>

      {/* Right */}
      <div className="flex items-center gap-3">
        {/* Live */}
        <div className="hidden xs:flex items-center gap-1.5 text-[10px] font-semibold text-[#2dc653]">
          <span className="live-dot" />
          LIVE
        </div>

        {/* Timestamp */}
        <div
          className="hidden sm:block font-mono text-[11px] text-t1 bg-b0 border border-bd
                        px-3 py-1.5 rounded-md"
        >
          {lastTime}
        </div>
        <div
          className="hidden sm:block font-mono text-[11px] text-t1 bg-b0 border border-bd
                        px-3 py-1.5 rounded-md"
        >
          {lastDate}
        </div>
      </div>
    </header>
  );
}

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
      className="flex items-center justify-between px-3 sm:px-5 h-[52px] sm:h-[64px] flex-shrink-0
                       bg-gradient-to-r from-b1 to-b2 border-b border-bd z-50 overflow-hidden"
    >
      {/* Left — Logo */}
      <div className="flex items-center gap-3">
        <div className="flex-shrink-0 flex items-center">
          {/* Desktop — logo panjang */}
          <img
            src="/logowhite_nobg.png"
            alt="URIS-AI"
            className="hidden sm:block h-12 w-auto max-w-[160px] object-contain"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
          {/* Mobile — icon saja */}
          <img
            src="/logowhite_single.png"
            alt="URIS-AI"
            className="sm:hidden h-9 w-9 object-contain"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
        </div>
        <div className="w-px h-6 sm:h-8 bg-bd flex-shrink-0" />
        <div className="hidden sm:block">
          <p className="text-[10px] text-t3 leading-tight">
            Urban Risk Intelligence System
          </p>
          <p className="text-[9px] text-t3/60 leading-tight">
            Jakarta &amp; Jawa Barat · Flood-Aware Mobility
          </p>
        </div>
        {/* Mobile: hanya nama singkat */}
        <div className="sm:hidden">
          <p className="text-[11px] font-bold text-t1 leading-tight">URIS-AI</p>
          <p className="text-[8px] text-t3 leading-tight">Urban Risk System</p>
        </div>
      </div>

      {/* Right */}
      <div className="flex items-center gap-3">
        {/* Home button — sembunyikan di mobile */}
        <a
          href="/"
          className="hidden sm:flex items-center gap-1.5 text-[10px] font-semibold text-t2
                     bg-b2 border border-bd hover:border-accent hover:text-t1
                     px-3 py-1.5 rounded-md transition-colors duration-150"
        >
          <svg
            className="w-3.5 h-3.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z" />
            <path d="M9 21V12h6v9" />
          </svg>
          Home
        </a>

        {/* Live */}
        <div className="hidden xs:flex items-center gap-1.5 text-[10px] font-semibold text-[#2dc653]">
          <span className="live-dot" />
          LIVE
        </div>

        {/* Timestamp — sembunyikan di mobile */}
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

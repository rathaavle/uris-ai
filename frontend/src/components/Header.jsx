import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

export default function Header() {
  const { dataUpdatedAt } = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboard,
  });

  const lastUpdate = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString("id-ID", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "--:--";

  return (
    <header
      className="flex items-center justify-between px-5 h-[64px] flex-shrink-0
                       bg-gradient-to-r from-b1 to-b2 border-b border-bd z-50"
    >
      {/* Left */}
      <div className="flex items-center gap-4">
        {/* Logo — lebih besar */}
        <div className="h-12 w-auto flex-shrink-0 flex items-center">
          <img
            src="/logowhite.jpg"
            alt="URIS-AI"
            className="h-12 w-auto max-w-[160px] object-contain"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
        </div>
        {/* Divider */}
        <div className="w-px h-8 bg-bd flex-shrink-0" />
        {/* Title */}
        <div>
          <p className="text-[10px] text-t3 leading-tight">
            Urban Risk Intelligence System
          </p>
          <p className="text-[9px] text-t3/60 leading-tight">
            Jakarta &amp; Jawa Barat · Flood-Aware Mobility
          </p>
        </div>
      </div>

      {/* Right */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-[10px] font-semibold text-[#2dc653]">
          <span className="live-dot" />
          LIVE
        </div>
        <div
          className="font-mono text-[10px] text-t3 bg-b0 border border-bd
                        px-3 py-1 rounded-md"
        >
          {lastUpdate}
        </div>
      </div>
    </header>
  );
}

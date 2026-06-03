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
      className="flex items-center justify-between px-5 h-[52px] flex-shrink-0
                       bg-gradient-to-r from-b1 to-b2 border-b border-bd z-50"
    >
      {/* Left */}
      <div className="flex items-center gap-3">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center font-extrabold
                        text-white text-sm shadow-lg flex-shrink-0
                        bg-gradient-to-br from-accent to-[#0096c7]"
        >
          🌊
        </div>
        <div>
          <h1
            className="text-sm font-bold bg-gradient-to-r from-t1 to-accent
                         bg-clip-text text-transparent leading-tight"
          >
            URIS-AI
          </h1>
          <p className="text-[10px] text-t3 leading-tight">
            Urban Risk Intelligence System · Jakarta &amp; Jawa Barat
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

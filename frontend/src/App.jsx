import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import { useStore } from "./store";
import DisclaimerModal from "./components/DisclaimerModal";
import LoadingScreen from "./components/LoadingScreen";
import Header from "./components/Header";
import KpiCards from "./components/KpiCards";
import Map from "./components/Map";
import Sidebar, { SidebarFilters, SidebarList } from "./components/Sidebar";
import DetailPanel from "./components/DetailPanel";

export default function App() {
  const { disclaimerDone, selectedRegionId } = useStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const { data, isLoading, isSuccess } = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboard,
  });

  const regions = data?.regions ?? [];
  const mapsKey = data?.maps_key ?? "";

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <DisclaimerModal />
      <LoadingScreen done={isSuccess} />
      <Header onMenuToggle={() => setSidebarOpen((o) => !o)} />
      <KpiCards />

      {/* Main layout */}
      <div className="flex flex-1 min-h-0 relative">
        {/* Map — full width di mobile, flex-1 di desktop */}
        <div className="flex-1 relative min-w-0">
          {isSuccess && <Map regions={regions} mapsKey={mapsKey} />}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-b0">
              <div className="text-t3 text-sm">Memuat peta...</div>
            </div>
          )}

          {/* Mobile: tombol buka sidebar */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="absolute top-3 right-3 z-20 lg:hidden
                       bg-b1/95 border border-bd text-t1 text-xs font-semibold
                       px-3 py-2 rounded-lg backdrop-blur-sm shadow-lg
                       flex items-center gap-1.5"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
            Wilayah
          </button>
        </div>

        {/* Sidebar desktop — tampil di lg+ */}
        <div className="hidden lg:flex">
          <Sidebar regions={regions} />
        </div>

        {/* Detail panel desktop */}
        {selectedRegionId && (
          <div className="hidden lg:flex">
            <DetailPanel regions={regions} />
          </div>
        )}

        {/* Mobile sidebar drawer */}
        {sidebarOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-30 bg-black/70 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            />

            {/* Drawer — dari bawah di mobile (<sm), dari kanan di tablet (sm+) */}
            <div
              className="fixed z-40 lg:hidden flex flex-col bg-b1
                            /* mobile: sheet dari bawah */
                            bottom-0 left-0 right-0 max-h-[85vh]
                            rounded-t-2xl border-t border-l border-r border-bd
                            /* tablet sm+: panel dari kanan */
                            sm:bottom-auto sm:top-0 sm:right-0 sm:left-auto
                            sm:h-full sm:w-[320px] sm:max-h-full
                            sm:rounded-none sm:border-t-0 sm:border-l sm:border-r-0 sm:border-b-0"
            >
              {/* Drag handle — mobile only */}
              <div className="sm:hidden flex justify-center pt-2.5 pb-1.5 flex-shrink-0">
                <div className="w-10 h-1 rounded-full bg-ba/60" />
              </div>

              {/* Header drawer */}
              <div
                className="flex items-center justify-between px-4 py-3
                              border-b border-bd flex-shrink-0"
              >
                <span className="text-xs font-bold text-t2 uppercase tracking-wider">
                  Daftar Wilayah
                </span>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="w-7 h-7 flex items-center justify-center
                             text-t3 hover:text-t1 hover:bg-b2
                             rounded-md transition-colors text-sm"
                >
                  ✕
                </button>
              </div>

              {/* Content — filter + scrollable list */}
              <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
                <SidebarFilters />
                <SidebarList
                  regions={regions}
                  onSelect={() => setSidebarOpen(false)}
                />
              </div>
            </div>
          </>
        )}

        {/* Mobile detail panel — full screen overlay */}
        {selectedRegionId && (
          <div
            className="fixed inset-0 z-50 lg:hidden flex flex-col bg-b1 overflow-hidden"
            style={{ height: "100dvh" }}
          >
            <DetailPanel regions={regions} fullscreen />
          </div>
        )}
      </div>
    </div>
  );
}

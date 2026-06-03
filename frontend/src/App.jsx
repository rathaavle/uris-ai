import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import { useStore } from "./store";
import DisclaimerModal from "./components/DisclaimerModal";
import LoadingScreen from "./components/LoadingScreen";
import Header from "./components/Header";
import KpiCards from "./components/KpiCards";
import Map from "./components/Map";
import Sidebar from "./components/Sidebar";
import DetailPanel from "./components/DetailPanel";

export default function App() {
  const { disclaimerDone, selectedRegionId } = useStore();

  const { data, isLoading, isSuccess } = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboard,
  });

  const regions = data?.regions ?? [];
  const mapsKey = data?.maps_key ?? "";

  return (
    <div className="flex flex-col h-full">
      {/* Disclaimer — tampil pertama kali */}
      <DisclaimerModal />

      {/* Loading screen */}
      <LoadingScreen done={isSuccess} />

      {/* Header */}
      <Header />

      {/* KPI cards */}
      <KpiCards />

      {/* Main content */}
      <div className="flex flex-1 min-h-0">
        {/* Map */}
        <div className="flex-1 relative">
          {isSuccess && <Map regions={regions} mapsKey={mapsKey} />}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-b0">
              <div className="text-t3 text-sm">Memuat peta...</div>
            </div>
          )}
        </div>

        {/* Sidebar — selalu tampil */}
        <Sidebar regions={regions} />

        {/* Detail panel — muncul di kanan saat klik wilayah */}
        {selectedRegionId && <DetailPanel regions={regions} />}
      </div>
    </div>
  );
}

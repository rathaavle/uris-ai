import { useEffect, useRef } from "react";
import { useStore } from "../store";
import { getRiskColor } from "../utils";

/* global atlas */

const FLOOD_RADIUS = { TINGGI: 28, KRITIS: 36 };

export default function Map({ regions, mapsKey }) {
  const mapInstance = useRef(null);
  const dsRef = useRef(null);
  const floodDsRef = useRef(null);
  // Selalu simpan data terbaru di ref agar bisa diakses dari dalam closure
  const regionsRef = useRef([]);
  const selectedIdRef = useRef(null);
  const { selectedRegionId, setSelectedRegion } = useStore();

  // Sinkronisasi ref dengan prop/state terbaru
  regionsRef.current = regions;
  selectedIdRef.current = selectedRegionId;

  function renderMarkers(regionList, selectedId) {
    const ds = dsRef.current;
    const fds = floodDsRef.current;
    if (!ds || !fds || !regionList.length) return;

    ds.clear();
    fds.clear();

    const markers = [];
    const floods = [];

    regionList.forEach((r) => {
      if (!r.latitude || !r.longitude) return;
      const color = getRiskColor(r.risk_category);
      const isSelected = r.region_id === selectedId;
      const pt = new atlas.data.Point([r.longitude, r.latitude]);

      markers.push(
        new atlas.data.Feature(pt, {
          id: r.region_id,
          label: Math.round(r.urban_risk_score).toString(),
          color,
          stroke: isSelected ? "#ffffff" : color,
          sw: isSelected ? 3 : 1.5,
        }),
      );

      if (r.risk_category === "TINGGI" || r.risk_category === "KRITIS") {
        floods.push(
          new atlas.data.Feature(pt, {
            c: color,
            r: FLOOD_RADIUS[r.risk_category] || 28,
          }),
        );
      }
    });

    ds.add(markers);
    fds.add(floods);
  }

  // Init map — hanya sekali saat mapsKey tersedia
  useEffect(() => {
    if (!mapsKey || mapInstance.current) return;

    const map = new atlas.Map("azure-map", {
      center: [106.8456, -6.2088],
      zoom: 10,
      language: "id-ID",
      style: "night",
      authOptions: { authType: "subscriptionKey", subscriptionKey: mapsKey },
    });

    map.events.add("ready", () => {
      const floodDs = new atlas.source.DataSource();
      const ds = new atlas.source.DataSource();
      map.sources.add(floodDs);
      map.sources.add(ds);

      map.layers.add(
        new atlas.layer.BubbleLayer(floodDs, null, {
          radius: ["get", "r"],
          color: ["get", "c"],
          opacity: 0.14,
          strokeColor: ["get", "c"],
          strokeWidth: 1.5,
          strokeOpacity: 0.32,
        }),
      );

      map.layers.add(
        new atlas.layer.SymbolLayer(ds, null, {
          iconOptions: { image: "none" },
          textOptions: {
            textField: ["get", "label"],
            color: "#ffffff",
            size: 10,
            font: ["StandardFont-Bold"],
            offset: [0, 0],
          },
        }),
      );

      const bubble = new atlas.layer.BubbleLayer(ds, null, {
        radius: 14,
        color: ["get", "color"],
        strokeColor: ["get", "stroke"],
        strokeWidth: ["get", "sw"],
        opacity: 0.85,
      });
      map.layers.add(bubble);

      map.events.add("click", bubble, (e) => {
        const props = e.shapes?.[0]?.getProperties();
        if (props?.id) setSelectedRegion(props.id);
      });
      map.events.add("mouseover", bubble, () => {
        map.getCanvasContainer().style.cursor = "pointer";
      });
      map.events.add("mouseout", bubble, () => {
        map.getCanvasContainer().style.cursor = "grab";
      });

      dsRef.current = ds;
      floodDsRef.current = floodDs;
      mapInstance.current = map;

      // Render langsung pakai data terbaru dari ref
      renderMarkers(regionsRef.current, selectedIdRef.current);
    });
  }, [mapsKey]);

  // Re-render saat regions berubah (setelah map sudah ready)
  useEffect(() => {
    if (!dsRef.current || !regions.length) return;
    renderMarkers(regions, selectedRegionId);
  }, [regions, selectedRegionId]);

  // Fly to selected
  useEffect(() => {
    if (!selectedRegionId || !mapInstance.current) return;
    const r = regions.find((x) => x.region_id === selectedRegionId);
    if (r?.latitude) {
      mapInstance.current.setCamera({
        center: [r.longitude, r.latitude],
        zoom: 13,
        type: "ease",
        duration: 600,
      });
    }
  }, [selectedRegionId]);

  return (
    <div className="relative w-full h-full">
      <div id="azure-map" className="w-full h-full bg-b0" />

      {/* Legend — pojok kiri bawah, naik agar tidak nutup watermark Azure */}
      <div
        className="absolute bottom-10 left-3 bg-b1/95 border border-bd
                      rounded-lg px-3 py-2.5 backdrop-blur-sm z-10"
      >
        <p className="text-[9px] text-t3 uppercase tracking-[0.7px] font-semibold mb-1.5">
          Tingkat Risiko
        </p>
        {[
          ["Rendah (0–25)", "#2dc653"],
          ["Sedang (26–50)", "#f4a621"],
          ["Tinggi (51–75)", "#f25c54"],
          ["Kritis (76–100)", "#b44fd4"],
        ].map(([label, color]) => (
          <div key={label} className="flex items-center gap-1.5 mb-1 last:mb-0">
            <span
              className="w-2.5 h-2.5 rounded-full flex-shrink-0"
              style={{ background: color }}
            />
            <span className="text-[10px] text-t2">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

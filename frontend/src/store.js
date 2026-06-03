import { create } from "zustand";

export const useStore = create((set) => ({
  selectedRegionId: null,
  cityFilter: "Semua",
  search: "",
  disclaimerDone:
    typeof sessionStorage !== "undefined"
      ? !!sessionStorage.getItem("urisai_disclaimer_ok")
      : false,

  setSelectedRegion: (id) => set({ selectedRegionId: id }),
  clearSelectedRegion: () => set({ selectedRegionId: null }),
  setCityFilter: (city) => set({ cityFilter: city }),
  setSearch: (q) => set({ search: q }),
  acceptDisclaimer: () => {
    sessionStorage.setItem("urisai_disclaimer_ok", "1");
    set({ disclaimerDone: true });
  },
}));

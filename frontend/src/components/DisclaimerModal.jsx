import { useStore } from "../store";

export default function DisclaimerModal() {
  const { disclaimerDone, acceptDisclaimer } = useStore();
  if (disclaimerDone) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="bg-b1 border border-bd rounded-2xl p-8 max-w-md w-[90%] shadow-2xl">
        <div className="text-3xl mb-4">⚠️</div>
        <h2 className="text-xl font-extrabold text-t1 mb-3">
          Perhatian — Data Simulasi
        </h2>
        <p className="text-t2 text-sm leading-relaxed mb-6">
          Data pada sistem ini merupakan{" "}
          <strong className="text-t1">data simulasi</strong> untuk keperluan
          demo. Pada implementasi produksi, data akan menggunakan sumber
          real-time dari <strong className="text-t1">BMKG</strong>,{" "}
          <strong className="text-t1">PetaBencana</strong>, dan{" "}
          <strong className="text-t1">OpenStreetMap</strong>.
          <br />
          <br />
          Gunakan data ini hanya sebagai{" "}
          <strong className="text-t1">acuan tampilan</strong> sistem. Keputusan
          resmi tetap mengacu pada informasi dari{" "}
          <strong className="text-t1">BPBD</strong> dan{" "}
          <strong className="text-t1">BMKG</strong>.
        </p>
        <button
          onClick={acceptDisclaimer}
          className="btn-accent w-full py-3 text-sm"
        >
          Saya Mengerti
        </button>
      </div>
    </div>
  );
}

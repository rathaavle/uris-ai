import { useNavigate } from "react-router-dom";

const FEATURES = [
  {
    img: "/floodwater.png",
    title: "Prediksi Risiko Banjir",
    desc: "Model ML berbasis data cuaca BMKG dan historis banjir Jakarta & Jawa Barat.",
  },
  {
    img: "/urbanrisk.png",
    title: "Urban Risk Score",
    desc: "Indikator risiko terpadu 0–100 per wilayah, gabungan banjir, kemacetan, dan aksesibilitas.",
  },
  {
    img: "/traffic.png",
    title: "Analisis Dampak Lalu Lintas",
    desc: "Identifikasi ruas jalan terdampak dari 27.835 data jalan OpenStreetMap.",
  },
  {
    img: "/publicservice.png",
    title: "Aksesibilitas Fasilitas",
    desc: "Pantau 11.233 fasilitas publik — RS, puskesmas, sekolah, kantor pemerintah.",
  },
  {
    img: "/roadsafe.png",
    title: "Rute Aman",
    desc: "Rekomendasi rute alternatif yang menghindari wilayah risiko Tinggi dan Kritis.",
  },
  {
    img: "/dashboard.png",
    title: "Dashboard Real-time",
    desc: "Visualisasi peta interaktif Azure Maps dengan auto-refresh setiap 15 menit.",
  },
];

const STATS = [
  { val: "25", label: "Wilayah Dipantau" },
  { val: "27.835", label: "Ruas Jalan" },
  { val: "11.233", label: "Fasilitas Publik" },
  { val: "432", label: "Data Cuaca BMKG" },
];

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-b0 flex flex-col overflow-x-hidden">
      {/* ── Navbar ── */}
      <nav className="sticky top-0 z-50 bg-b0/80 backdrop-blur-md border-b border-bd/60">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-3 flex items-center justify-between">
          <img
            src="/logowhite_nobg.png"
            alt="URIS-AI"
            className="hidden sm:block h-14 w-auto object-contain"
          />
          <img
            src="/logowhite_single.png"
            alt="URIS-AI"
            className="sm:hidden h-9 w-auto object-contain"
            onError={(e) => {
              e.currentTarget.src = "/logo.png";
            }}
          />
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative flex flex-col items-center text-center px-6 pt-16 sm:pt-24 pb-14 sm:pb-20 overflow-hidden">
        {/* background glow blobs */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div
            className="absolute -top-24 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full opacity-[0.07]"
            style={{
              background:
                "radial-gradient(circle, #00b4d8 0%, transparent 70%)",
            }}
          />
          <div
            className="absolute top-40 -right-32 w-72 h-72 rounded-full opacity-[0.06]"
            style={{
              background:
                "radial-gradient(circle, #b44fd4 0%, transparent 70%)",
            }}
          />
        </div>

        {/* badge */}
        <div className="relative inline-flex items-center gap-2 bg-accent/10 border border-accent/30 text-accent text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          Data Simulasi · Demo Version
        </div>

        <h1 className="relative text-3xl xs:text-4xl sm:text-5xl md:text-6xl font-extrabold text-t1 leading-tight mb-5 max-w-4xl">
          Urban Risk Intelligence
          <br />
          <span className="bg-gradient-to-r from-accent via-[#48cae4] to-[#0096c7] bg-clip-text text-transparent">
            for Smarter Urban Resilience
          </span>
        </h1>

        <p className="relative text-t2 text-sm sm:text-base max-w-2xl leading-relaxed mb-10 px-2">
          Sistem berbasis AI yang mengintegrasikan data cuaca, historis banjir,
          jaringan jalan, dan fasilitas publik untuk memprediksi dan merespons
          risiko urban di{" "}
          <strong className="text-t1">Jakarta &amp; Jawa Barat</strong>.
        </p>

        <div className="relative flex items-center gap-3 sm:gap-4 flex-wrap justify-center">
          <button
            onClick={() => navigate("/dashboard")}
            className="btn-accent px-7 sm:px-9 py-3 text-sm sm:text-base shadow-lg shadow-accent/20"
          >
            Buka Dashboard
          </button>
          <a
            href="https://github.com/rathaavle/uris-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-t2 hover:text-t1 text-sm border border-bd hover:border-accent px-5 sm:px-6 py-3 rounded-lg transition-colors duration-150"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
            </svg>
            GitHub
          </a>
        </div>
      </section>

      {/* ── Stats strip ── */}
      <section className="px-5 sm:px-8 pb-14 sm:pb-18">
        <div className="max-w-3xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
          {STATS.map(({ val, label }) => (
            <div
              key={label}
              className="card p-4 sm:p-5 text-center rounded-xl border border-bd hover:border-accent/40 transition-colors duration-200"
            >
              <p className="font-mono text-2xl sm:text-3xl font-extrabold text-accent leading-none">
                {val}
              </p>
              <p className="text-[11px] text-t3 mt-1.5 leading-tight">
                {label}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section className="px-5 sm:px-8 pt-6 sm:pt-10 pb-16 sm:pb-20 max-w-6xl mx-auto w-full">
        <div className="text-center mb-8 sm:mb-12">
          <h2 className="text-xl sm:text-2xl font-extrabold text-t1 mb-2">
            Fitur Utama
          </h2>
          <p className="text-t2 text-sm max-w-lg mx-auto">
            Enam modul analitik terintegrasi untuk memahami dan merespons risiko
            urban secara komprehensif.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="group bg-white border border-gray-200 p-5 rounded-xl flex flex-col gap-4 hover:border-accent/60 hover:shadow-md transition-all duration-200 hover:-translate-y-0.5"
            >
              {/* image icon */}
              <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-xl flex items-center justify-center overflow-hidden">
                <img
                  src={f.img}
                  alt={f.title}
                  className="w-full h-full object-contain"
                />
              </div>

              <div>
                <h3 className="text-sm font-bold text-gray-800 mb-1.5">
                  {f.title}
                </h3>
                <p className="text-xs text-gray-500 leading-relaxed">
                  {f.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works strip ── */}
      <section className="px-5 sm:px-8 pb-16 sm:pb-20 max-w-6xl mx-auto w-full">
        <div className="card rounded-2xl px-6 sm:px-10 py-8 sm:py-10 border border-bd bg-b1">
          <h2 className="text-center text-lg sm:text-xl font-extrabold text-t1 mb-8">
            Cara Kerja Sistem
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
            {[
              {
                step: "01",
                title: "Kumpul Data",
                desc: "BMKG cuaca, historis banjir, OSM jalan & fasilitas dikumpulkan dan dibersihkan secara otomatis.",
              },
              {
                step: "02",
                title: "Analisis AI",
                desc: "Model ML menghitung skor risiko banjir, kemacetan, dan aksesibilitas per wilayah.",
              },
              {
                step: "03",
                title: "Visualisasi",
                desc: "Hasil ditampilkan dalam dashboard peta interaktif dengan rekomendasi rute aman.",
              },
            ].map((item) => (
              <div key={item.step} className="flex flex-col items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-accent/10 border border-accent/30 flex items-center justify-center">
                  <span className="font-mono text-xs font-bold text-accent">
                    {item.step}
                  </span>
                </div>
                <h4 className="font-bold text-t1 text-sm">{item.title}</h4>
                <p className="text-xs text-t2 leading-relaxed max-w-xs">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="text-center pb-14 sm:pb-20 px-5 sm:px-6">
        <div className="max-w-lg mx-auto card rounded-2xl p-6 sm:p-10 border border-bd bg-b1 relative overflow-hidden">
          {/* subtle glow */}
          <div
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                "radial-gradient(ellipse at 50% 0%, rgba(0,180,216,0.08) 0%, transparent 70%)",
            }}
          />
          <h3 className="relative text-base sm:text-lg font-extrabold text-t1 mb-2">
            Siap Menjelajahi Dashboard?
          </h3>
          <p className="relative text-t2 text-sm mb-6 leading-relaxed">
            Lihat peta risiko 25 wilayah secara real-time dengan visualisasi
            interaktif Azure Maps.
          </p>
          <button
            onClick={() => navigate("/dashboard")}
            className="relative btn-accent px-8 py-3 text-sm w-full sm:w-auto shadow-lg shadow-accent/20"
          >
            Buka Dashboard Sekarang →
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="text-center py-5 border-t border-bd/50 text-[10px] text-t3 px-4">
        © 2026 URIS-AI · Data Simulasi untuk Keperluan Demo ·{" "}
        <span className="text-accent">
          From Data to Decision for Smarter Urban Resilience
        </span>
      </footer>
    </div>
  );
}

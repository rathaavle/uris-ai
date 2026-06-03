import { useNavigate } from "react-router-dom";

const FEATURES = [
  {
    icon: "🌊",
    title: "Prediksi Risiko Banjir",
    desc: "Model ML berbasis data cuaca BMKG dan historis banjir Jakarta & Jawa Barat.",
  },
  {
    icon: "📊",
    title: "Urban Risk Score",
    desc: "Indikator risiko terpadu 0–100 per wilayah, gabungan banjir, kemacetan, dan aksesibilitas.",
  },
  {
    icon: "🚗",
    title: "Analisis Dampak Lalu Lintas",
    desc: "Identifikasi ruas jalan terdampak dari 27.835 data jalan OpenStreetMap.",
  },
  {
    icon: "🏥",
    title: "Aksesibilitas Fasilitas",
    desc: "Pantau 11.233 fasilitas publik — RS, puskesmas, sekolah, kantor pemerintah.",
  },
  {
    icon: "🗺️",
    title: "Rute Aman",
    desc: "Rekomendasi rute alternatif yang menghindari wilayah risiko Tinggi dan Kritis.",
  },
  {
    icon: "⚡",
    title: "Dashboard Real-time",
    desc: "Visualisasi peta interaktif Azure Maps dengan auto-refresh setiap 15 menit.",
  },
];

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-b0 flex flex-col">
      {/* Nav — putih dengan logo berwarna */}
      <nav
        className="flex items-center px-5 sm:px-8 py-3
                      bg-white border-b border-gray-100 shadow-sm sticky top-0 z-50"
      >
        {/* Logo — berwarna di desktop, single icon di mobile */}
        <img
          src="/logo.png"
          alt="URIS-AI"
          className="hidden sm:block h-20 w-auto object-contain"
        />
        <img
          src="/logo_single.png"
          alt="URIS-AI"
          className="sm:hidden h-10 w-auto object-contain"
          onError={(e) => {
            e.currentTarget.src = "/logo.png";
          }}
        />
      </nav>

      {/* Hero */}
      <section className="flex flex-col items-center text-center px-6 pt-16 sm:pt-20 pb-12 sm:pb-16">
        <div
          className="inline-flex items-center gap-2 bg-accent/10 border border-accent/30
                        text-accent text-xs font-semibold px-3 py-1.5 rounded-full mb-5 sm:mb-6"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          Data Simulasi · Demo Version
        </div>

        <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-t1 leading-tight mb-4 max-w-3xl">
          Urban Risk Intelligence System
          <br />
          <span className="bg-gradient-to-r from-accent to-[#0096c7] bg-clip-text text-transparent">
            for Smarter Urban Resilience
          </span>
        </h1>

        <p className="text-t2 text-sm sm:text-base max-w-xl leading-relaxed mb-10 sm:mb-8 px-7">
          Sistem berbasis AI yang mengintegrasikan data cuaca, historis banjir,
          jaringan jalan, dan fasilitas publik untuk memprediksi dan merespons
          risiko urban di{" "}
          <strong className="text-t1">Jakarta & Jawa Barat</strong>.
        </p>

        <div className="flex items-center gap-3 sm:gap-4 flex-wrap justify-center">
          <button
            onClick={() => navigate("/dashboard")}
            className="btn-accent px-6 sm:px-8 py-3 text-sm sm:text-base"
          >
            Buka Dashboard
          </button>
          <a
            href="https://github.com/rathaavle/uris-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-t2 hover:text-t1 text-sm
                       border border-bd hover:border-accent px-5 sm:px-6 py-3 rounded-lg
                       transition-colors duration-150"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483
                       0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466
                       -.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832
                       .092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688
                       -.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115
                       2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595
                       1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012
                       2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
              />
            </svg>
            GitHub
          </a>
        </div>
      </section>

      {/* Stats */}
      <section
        className="grid grid-cols-2 sm:flex sm:justify-center gap-4 sm:gap-8
                          px-6 pb-10 sm:pb-14"
      >
        {[
          ["25", "Wilayah Dipantau"],
          ["27.835", "Ruas Jalan"],
          ["11.233", "Fasilitas Publik"],
          ["432", "Data Cuaca BMKG"],
        ].map(([val, label]) => (
          <div
            key={label}
            className="text-center card p-4 sm:p-0 sm:border-0 sm:bg-transparent sm:rounded-none"
          >
            <p className="font-mono text-2xl sm:text-3xl font-extrabold text-accent">
              {val}
            </p>
            <p className="text-xs text-t3 mt-1">{label}</p>
          </div>
        ))}
      </section>

      {/* Features */}
      <section className="px-5 sm:px-8 pb-12 sm:pb-16 max-w-5xl mx-auto w-full">
        <h2 className="text-center text-lg sm:text-xl font-extrabold text-t1 mb-6 sm:mb-8">
          Fitur Utama
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
          {FEATURES.map((f) => (
            <div key={f.title} className="card p-4 sm:p-5">
              <div className="text-xl sm:text-2xl mb-2 sm:mb-3">{f.icon}</div>
              <h3 className="text-sm font-bold text-t1 mb-1.5">{f.title}</h3>
              <p className="text-xs text-t2 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="text-center pb-12 sm:pb-16 px-5 sm:px-6">
        <div className="card p-6 sm:px-10 sm:py-8 max-w-lg mx-auto">
          <h3 className="text-base sm:text-lg font-extrabold text-t1 mb-2">
            Siap Menjelajahi Dashboard?
          </h3>
          <p className="text-t2 text-sm mb-5 sm:mb-6">
            Lihat peta risiko 25 wilayah secara real-time dengan visualisasi
            interaktif Azure Maps.
          </p>
          <button
            onClick={() => navigate("/dashboard")}
            className="btn-accent px-8 py-3 text-sm w-full"
          >
            Buka Dashboard Sekarang →
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="text-center py-4 border-t border-bd/50 text-[10px] text-t3 px-4">
        © 2026 URIS-AI · Data Simulasi untuk Keperluan Demo ·{" "}
        <span className="text-accent">
          From Data to Decision for Smarter Urban Resilience
        </span>
      </footer>
    </div>
  );
}

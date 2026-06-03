import { useState, useEffect } from "react";

const STEPS = [
  "Menghubungkan ke server...",
  "Memuat data wilayah...",
  "Menyiapkan peta Azure Maps...",
  "Menghitung Urban Risk Score...",
  "Siap",
];

export default function LoadingScreen({ done }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (done) {
      setStep(STEPS.length - 1);
      return;
    }
    const t = setInterval(
      () => setStep((s) => Math.min(s + 1, STEPS.length - 2)),
      800,
    );
    return () => clearInterval(t);
  }, [done]);

  if (done && step === STEPS.length - 1) return null;

  return (
    <div className="fixed inset-0 z-[9998] flex items-center justify-center bg-b0">
      <div
        className="bg-b1 border border-bd rounded-xl px-8 py-6 min-w-[260px]
                      shadow-2xl space-y-2"
      >
        <p className="text-xs font-bold text-t2 uppercase tracking-widest mb-3">
          URIS-AI memuat...
        </p>
        {STEPS.map((s, i) => (
          <div
            key={s}
            className={`flex items-center gap-2.5 text-[11px] transition-colors
                                   ${i < step ? "text-[#2dc653]" : i === step ? "text-t1" : "text-t3"}`}
          >
            <span className="w-3 text-center font-mono">
              {i < step ? "✓" : i === step ? "●" : "○"}
            </span>
            {s}
          </div>
        ))}
      </div>
    </div>
  );
}

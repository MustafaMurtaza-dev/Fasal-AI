"use client";
import { useState, useEffect } from "react";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Loader2,
  BarChart3,
  Sparkles,
  Info,
} from "lucide-react";
import { marketAPI } from "@/lib/api";

const crops = [
  { id: "wheat", name: "Wheat", urdu: "گندم", icon: "🌾" },
  { id: "rice", name: "Rice", urdu: "چاول", icon: "🌾" },
  { id: "cotton", name: "Cotton", urdu: "کپاس", icon: "🏵️" },
  { id: "maize", name: "Maize", urdu: "مکئی", icon: "🌽" },
  { id: "potato", name: "Potato", urdu: "آلو", icon: "🥔" },
  { id: "tomato", name: "Tomato", urdu: "ٹماٹر", icon: "🍅" },
  { id: "onion", name: "Onion", urdu: "پیاز", icon: "🧅" },
  { id: "sugarcane", name: "Sugarcane", urdu: "گنا", icon: "🎋" },
];

/** Format number as PKR with commas */
function formatPKR(amount: number | undefined | null): string {
  if (amount === null || amount === undefined || isNaN(amount)) return "—";
  return `PKR ${Math.round(amount).toLocaleString("en-PK")}`;
}

/** Render markdown bold **text** in analysis */
function renderAnalysis(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-bold text-gray-800">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

export default function Market() {
  const [crop, setCrop] = useState("wheat");
  const [days, setDays] = useState(7);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await marketAPI.predict(crop, days);
      setData(result);
    } catch (err: any) {
      setError(err?.message || "Failed to load market data");
      setData(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [crop, days]);

  const selectedCrop = crops.find((c) => c.id === crop);

  // Trend icon & colors
  const TIcon =
    data?.trend === "increasing"
      ? TrendingUp
      : data?.trend === "decreasing"
      ? TrendingDown
      : Minus;

  const tColor =
    data?.trend === "increasing"
      ? "text-green-600"
      : data?.trend === "decreasing"
      ? "text-red-500"
      : "text-gray-500";

  const tBg =
    data?.trend === "increasing"
      ? "bg-green-50 border-green-100"
      : data?.trend === "decreasing"
      ? "bg-red-50 border-red-100"
      : "bg-gray-50 border-gray-100";

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* ── Header ── */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-1.5 rounded-full text-sm font-semibold mb-3">
          <BarChart3 className="w-4 h-4" />
          Market Intelligence
        </div>
        <h2 className="text-3xl font-extrabold text-gray-800 mb-1">
          Market <span className="text-gradient">Prices & Predictions</span>
        </h2>
        <p
          className="text-sm text-gray-500 font-medium"
          style={{ direction: "rtl" }}
        >
          منڈی قیمتیں اور AI پیشن گوئی
        </p>
      </div>

      {/* ── Crop Selector ── */}
      <div className="glass p-4 mb-6">
        <div className="flex flex-wrap gap-2">
          {crops.map((c) => (
            <button
              key={c.id}
              onClick={() => setCrop(c.id)}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all ${
                crop === c.id
                  ? "bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg shadow-green-600/25"
                  : "bg-gray-50 text-gray-600 hover:bg-green-50 hover:text-green-700 border border-gray-100"
              }`}
            >
              <span className="text-base">{c.icon}</span>
              <span>{c.name}</span>
              <span className="text-[10px] opacity-70">{c.urdu}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Loading State ── */}
      {loading ? (
        <div className="glass p-16 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-green-600 mx-auto" />
          <p className="text-sm text-gray-400 mt-3">Loading market data...</p>
        </div>
      ) : error ? (
        /* ── Error State ── */
        <div className="glass p-16 text-center">
          <BarChart3 className="w-12 h-12 text-red-200 mx-auto mb-3" />
          <p className="text-red-500 font-medium">{error}</p>
          <button
            onClick={fetchData}
            className="mt-4 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 transition"
          >
            Retry
          </button>
        </div>
      ) : data ? (
        <div className="space-y-5">
          {/* ── Top Stats Row ── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 stagger">
            {/* Current Price */}
            <div className="glass p-5 stat-glow col-span-2 md:col-span-1">
              <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">
                Current Price
              </p>
              <p className="text-3xl font-extrabold text-gray-800 mt-2">
                <span className="text-gradient">
                  {formatPKR(data.current_price_pkr)}
                </span>
              </p>
              <p className="text-[11px] text-gray-400 mt-1 font-medium">
                {data.unit || "per 40 kg (1 maund)"}
              </p>
            </div>

            {/* Trend */}
            <div className="glass p-5 stat-glow">
              <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">
                Trend
              </p>
              <div
                className={`inline-flex items-center gap-1.5 mt-3 px-3 py-2 rounded-xl border ${tBg} ${tColor}`}
              >
                <TIcon className="w-5 h-5" />
                <span className="text-sm font-extrabold capitalize">
                  {data.trend}
                </span>
              </div>
            </div>

            {/* Support Price */}
            <div className="glass p-5 stat-glow">
              <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">
                Support Price
              </p>
              <p className="text-xl font-extrabold text-gray-700 mt-2">
                {data.support_price_pkr
                  ? formatPKR(data.support_price_pkr)
                  : "N/A"}
              </p>
              <p className="text-[10px] text-gray-400 mt-1">
                {data.support_price_pkr ? "Govt. MSP" : "No MSP set"}
              </p>
            </div>

            {/* Season & Mandi */}
            <div className="glass p-5 stat-glow">
              <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">
                Season
              </p>
              <p className="text-lg font-bold text-gray-700 mt-2">
                {data.season || "—"}
              </p>
              <p className="text-[10px] text-gray-400 mt-1">
                {data.mandi || "All Pakistan"}
              </p>
            </div>
          </div>

          {/* ── Forecast Table ── */}
          <div className="glass p-6 stat-glow fade-in-up">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-sm flex items-center gap-2">
                📈 {days}-Day Price Forecast
                <span className="text-[10px] text-gray-400 font-normal">
                  ({selectedCrop?.name} — {selectedCrop?.urdu})
                </span>
              </h3>
              <div className="flex gap-1.5 bg-gray-100 p-1 rounded-xl">
                {[7, 14, 30].map((d) => (
                  <button
                    key={d}
                    onClick={() => setDays(d)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      days === d
                        ? "bg-white text-green-700 shadow-sm"
                        : "text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    {d}d
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
              {/* Column Headers */}
              <div className="flex justify-between items-center px-3 py-2 text-[10px] font-bold text-gray-400 uppercase tracking-wider border-b border-gray-100">
                <span className="w-24">Date</span>
                <div className="flex gap-4 items-center">
                  <span className="w-28 text-right">Predicted</span>
                  <span className="w-36 text-right hidden sm:block">
                    Range
                  </span>
                  <span className="w-16 text-right">Confidence</span>
                </div>
              </div>

              {data.predictions?.map((p: any, i: number) => {
                // Support both field naming conventions
                const predictedPrice =
                  p.predicted_price_pkr ?? p.predicted_price ?? 0;
                const confLow =
                  p.confidence_interval_low ??
                  p.price_range_low_pkr ??
                  Math.round(predictedPrice * 0.92);
                const confHigh =
                  p.confidence_interval_high ??
                  p.price_range_high_pkr ??
                  Math.round(predictedPrice * 1.08);
                const conf =
                  p.confidence ?? Math.max(0.6, 0.95 - i * 0.01);

                const confColor =
                  conf >= 0.85
                    ? "text-green-600 bg-green-50"
                    : conf >= 0.7
                    ? "text-yellow-600 bg-yellow-50"
                    : "text-red-500 bg-red-50";

                return (
                  <div
                    key={i}
                    className="flex justify-between items-center p-3 bg-gray-50 hover:bg-green-50 rounded-xl text-sm transition group"
                  >
                    <span className="text-gray-500 font-medium text-[13px] w-24">
                      {p.date}
                    </span>
                    <div className="flex items-center gap-4">
                      <span className="font-bold text-gray-800 group-hover:text-green-700 transition w-28 text-right">
                        {formatPKR(predictedPrice)}
                      </span>
                      <span className="text-[11px] text-gray-400 w-36 text-right hidden sm:block">
                        {formatPKR(confLow)} — {formatPKR(confHigh)}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full w-16 text-center ${confColor}`}
                      >
                        {(conf * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── AI Analysis ── */}
          <div className="glass p-6 stat-glow fade-in-up">
            <h3 className="font-bold text-sm mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-green-600" />
              AI Market Analysis
            </h3>

            {/* Render analysis with **bold** support */}
            <div className="text-sm text-gray-600 leading-relaxed space-y-2">
              {(data.ai_analysis || "No analysis available.")
                .split("\n\n")
                .map((para: string, i: number) => (
                  <p key={i}>{renderAnalysis(para)}</p>
                ))}
            </div>

            {/* Best Sell Window */}
            {data.best_sell_window && (
              <div className="mt-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100">
                <p className="text-sm font-semibold text-green-800 flex items-center gap-2">
                  🎯 Best Selling Window:
                </p>
                <p className="text-sm font-bold text-green-900 mt-1">
                  {data.best_sell_window}
                </p>
              </div>
            )}

            {/* Disclaimer */}
            {data.disclaimer && (
              <div className="mt-3 flex items-start gap-2 text-[11px] text-gray-400">
                <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                <span>{data.disclaimer}</span>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* ── Empty State ── */
        <div className="glass p-16 text-center">
          <BarChart3 className="w-12 h-12 text-green-200 mx-auto mb-3" />
          <p className="text-gray-400">
            Select a crop to view market predictions
          </p>
        </div>
      )}
    </div>
  );
}
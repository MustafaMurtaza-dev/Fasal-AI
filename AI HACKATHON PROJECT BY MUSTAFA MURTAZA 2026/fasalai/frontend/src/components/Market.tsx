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
  Calendar,
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

function formatPKR(amount: number | undefined | null): string {
  if (amount === null || amount === undefined || isNaN(amount)) return "—";
  return `Rs. ${Math.round(amount).toLocaleString("en-PK")}`;
}

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

const Skeleton = () => (
  <div className="animate-pulse space-y-6">
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="glass h-24 rounded-2xl bg-gray-100/50"></div>
      ))}
    </div>
    <div className="glass h-64 rounded-2xl bg-gray-100/50"></div>
    <div className="glass h-40 rounded-2xl bg-gray-100/50"></div>
  </div>
);

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

  // Trend logic
  const isUp = data?.trend === "increasing";
  const isDown = data?.trend === "decreasing";
  const TIcon = isUp ? TrendingUp : isDown ? TrendingDown : Minus;
  const tColor = isUp ? "text-green-600" : isDown ? "text-red-500" : "text-gray-500";
  const tBg = isUp
    ? "bg-green-50 border-green-200"
    : isDown
      ? "bg-red-50 border-red-200"
      : "bg-gray-50 border-gray-200";

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* ── Header ── */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-800 px-4 py-1.5 rounded-full text-sm font-semibold mb-4 shadow-sm">
          <BarChart3 className="w-4 h-4" />
          Market Intelligence
        </div>
        <h2 className="text-3xl font-extrabold text-gray-900 mb-2">
          Market <span className="text-gradient">Prices & Predictions</span>
        </h2>
        <p className="text-sm text-gray-500 font-medium" style={{ direction: "rtl" }}>
          منڈی قیمتیں اور AI پیشن گوئی
        </p>
      </div>

      {/* ── Crop Selector ── */}
      <div className="glass p-2 mb-8 overflow-x-auto">
        <div className="flex gap-2 min-w-max">
          {crops.map((c) => (
            <button
              key={c.id}
              onClick={() => setCrop(c.id)}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all border ${crop === c.id
                  ? "bg-gradient-to-r from-green-600 to-emerald-600 text-white border-transparent shadow-lg shadow-green-600/20 transform scale-105"
                  : "bg-white text-gray-600 hover:bg-green-50 hover:text-green-700 hover:border-green-200 border-transparent"
                }`}
            >
              <span className="text-lg">{c.icon}</span>
              <span>{c.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Main Content ── */}
      {loading ? (
        <Skeleton />
      ) : error ? (
        <div className="glass p-12 text-center border-red-100 bg-red-50/30">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <BarChart3 className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-lg font-bold text-gray-800 mb-2">Data Unavailable</h3>
          <p className="text-red-600 mb-6">{error}</p>
          <button
            onClick={fetchData}
            className="px-6 py-2.5 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition shadow-lg shadow-red-600/20"
          >
            Try Again
          </button>
        </div>
      ) : data ? (
        <div className="space-y-6 fade-in-up">
          {/* ── Stats Grid ── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Current Price */}
            <div className="glass p-5 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition">
                <BarChart3 className="w-12 h-12 text-green-600" />
              </div>
              <p className="text-[11px] text-gray-400 font-bold uppercase tracking-wider">Current Price</p>
              <p className="text-2xl md:text-3xl font-black text-gray-800 mt-2">
                {formatPKR(data.current_price_pkr)}
              </p>
              <p className="text-[11px] text-gray-400 mt-1 font-medium">
                {data.unit || "per 40 kg"}
              </p>
            </div>

            {/* Trend */}
            <div className="glass p-5 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition">
                <TIcon className={`w-12 h-12 ${tColor}`} />
              </div>
              <p className="text-[11px] text-gray-400 font-bold uppercase tracking-wider">Market Trend</p>
              <div className={`inline-flex items-center gap-2 mt-3 px-3 py-1.5 rounded-lg border ${tBg}`}>
                <TIcon className={`w-4 h-4 ${tColor}`} />
                <span className={`text-sm font-bold capitalize ${tColor}`}>
                  {data.trend}
                </span>
              </div>
            </div>

            {/* Support Price */}
            <div className="glass p-5">
              <p className="text-[11px] text-gray-400 font-bold uppercase tracking-wider">Support Price</p>
              <p className="text-xl md:text-2xl font-bold text-gray-700 mt-2">
                {formatPKR(data.support_price_pkr)}
              </p>
              <p className="text-[10px] text-gray-400 mt-1">
                {data.support_price_pkr ? "Govt. Set Rate" : "Not Set"}
              </p>
            </div>

            {/* Season/Mandi */}
            <div className="glass p-5">
              <p className="text-[11px] text-gray-400 font-bold uppercase tracking-wider">Mandi Location</p>
              <p className="text-lg font-bold text-gray-800 mt-2 truncate">
                {data.mandi || "All Pakistan"}
              </p>
              <p className="text-[11px] text-gray-400 mt-1 flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {data.season || "Current Season"}
              </p>
            </div>
          </div>

          {/* ── Forecast Chart Table ── */}
          <div className="glass p-6 md:p-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <h3 className="font-bold text-lg flex items-center gap-2 text-gray-800">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  Price Forecast
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  AI-powered price predictions for next {days} days
                </p>
              </div>
              <div className="flex bg-gray-100 p-1 rounded-xl self-start">
                {[7, 14, 30].map((d) => (
                  <button
                    key={d}
                    onClick={() => setDays(d)}
                    className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${days === d
                        ? "bg-white text-green-700 shadow-sm"
                        : "text-gray-500 hover:text-gray-700"
                      }`}
                  >
                    {d} Days
                  </button>
                ))}
              </div>
            </div>

            <div className="overflow-hidden rounded-xl border border-gray-100">
              <div className="grid grid-cols-4 bg-gray-50/80 p-3 text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                <div>Date</div>
                <div className="text-right">Predicted</div>
                <div className="text-right hidden sm:block">Range</div>
                <div className="text-right">Confidence</div>
              </div>
              <div className="divide-y divide-gray-50 max-h-80 overflow-y-auto custom-scrollbar">
                {data.predictions?.map((p: any, i: number) => {
                  const price = p.predicted_price_pkr ?? p.predicted_price ?? 0;
                  const low = p.confidence_interval_low ?? Math.round(price * 0.92);
                  const high = p.confidence_interval_high ?? Math.round(price * 1.08);
                  const conf = p.confidence ?? 0.85;

                  return (
                    <div key={i} className="grid grid-cols-4 p-3.5 hover:bg-green-50/30 transition-colors items-center">
                      <div className="text-sm font-medium text-gray-600">{p.date}</div>
                      <div className="text-right font-bold text-gray-800">{formatPKR(price)}</div>
                      <div className="text-right text-xs text-gray-400 hidden sm:block">
                        {Math.round(low).toLocaleString()} - {Math.round(high).toLocaleString()}
                      </div>
                      <div className="text-right">
                        <span className={`inline-block px-2 py-0.5 rounded-md text-[10px] font-bold ${conf >= 0.8 ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
                          }`}>
                          {(conf * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* ── Analysis Card ── */}
          <div className="glass p-6 md:p-8 bg-gradient-to-br from-white to-green-50/30">
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2 text-gray-800">
              <Sparkles className="w-5 h-5 text-emerald-500" />
              AI Market Analysis
            </h3>

            <div className="prose prose-sm max-w-none text-gray-600 bg-white/50 p-4 rounded-xl border border-gray-100/50">
              {(data.ai_analysis || "No analysis available.").split("\n\n").map((para: string, i: number) => (
                <p key={i} className="mb-2 last:mb-0 leading-relaxed">{renderAnalysis(para)}</p>
              ))}
            </div>

            {data.best_sell_window && (
              <div className="mt-6 flex items-start gap-4 p-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/20">
                <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-xs font-medium text-emerald-100 uppercase tracking-wide">Recommendation</p>
                  <p className="font-bold text-lg mt-0.5">Best Time to Sell: {data.best_sell_window}</p>
                </div>
              </div>
            )}

            {data.disclaimer && (
              <div className="mt-6 flex items-center gap-2 text-xs text-gray-400 bg-gray-50 p-3 rounded-lg">
                <Info className="w-4 h-4 shrink-0" />
                <span>{data.disclaimer}</span>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* ── Empty State ── */
        <div className="glass p-20 text-center flex flex-col items-center justify-center min-h-[400px]">
          <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-6">
            <BarChart3 className="w-10 h-10 text-gray-300" />
          </div>
          <h3 className="text-xl font-bold text-gray-800 mb-2">Market Engine Ready</h3>
          <p className="text-gray-400">Select a crop above to generate AI price predictions</p>
        </div>
      )}
    </div>
  );
}
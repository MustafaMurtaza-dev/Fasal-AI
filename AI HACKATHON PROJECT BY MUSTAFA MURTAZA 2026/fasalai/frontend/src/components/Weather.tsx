"use client";
import { useState, useEffect, useCallback } from "react";
import {
  Cloud,
  Thermometer,
  Droplets,
  Wind,
  Loader2,
  AlertTriangle,
  Sun,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { weatherAPI } from "@/lib/api";

const cities = [
  "Lahore", "Faisalabad", "Multan", "Karachi", "Peshawar",
  "Rawalpindi", "Hyderabad", "Quetta", "Bahawalpur", "Sahiwal",
];

/* ─── Safe data extractors ─── */
function safeString(val: any, fallback = ""): string {
  if (typeof val === "string") return val;
  if (typeof val === "number") return String(val);
  if (val === null || val === undefined) return fallback;
  if (typeof val === "object") {
    return val.text || val.message || val.description || JSON.stringify(val);
  }
  return String(val);
}

function safeNumber(val: any, fallback = 0): number {
  if (typeof val === "number" && !isNaN(val)) return val;
  if (typeof val === "string") {
    const n = parseFloat(val);
    if (!isNaN(n)) return n;
  }
  return fallback;
}

function safeStringArray(val: any): string[] {
  if (!val) return [];
  if (typeof val === "string") return val.trim() ? [val] : [];
  if (!Array.isArray(val)) return [];
  return val
    .map((item: any) => {
      if (typeof item === "string") return item;
      if (typeof item === "object" && item !== null) {
        return item.action || item.text || item.recommendation || item.description || JSON.stringify(item);
      }
      return String(item);
    })
    .filter((s: string) => s && s.trim().length > 0);
}

export default function Weather() {
  const [city, setCity] = useState("Lahore");
  const [crop, setCrop] = useState("wheat");
  const [weather, setWeather] = useState<any>(null);
  const [impact, setImpact] = useState<any>(null);
  const [alerts, setAlerts] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch all three in parallel
      const results = await Promise.allSettled([
        weatherAPI.current(city),
        weatherAPI.cropImpact(city, crop),
        weatherAPI.alerts(city, crop),
      ]);

      // Weather — always try to get
      if (results[0].status === "fulfilled") {
        setWeather(results[0].value);
        console.log("🌤️ Weather:", results[0].value);
      } else {
        console.error("Weather failed:", results[0].reason);
        setWeather(null);
      }

      // Crop Impact
      if (results[1].status === "fulfilled") {
        setImpact(results[1].value);
        console.log("🌾 Impact:", results[1].value);
      } else {
        console.error("Impact failed:", results[1].reason);
        setImpact(null);
      }

      // Alerts
      if (results[2].status === "fulfilled") {
        setAlerts(results[2].value);
        console.log("⚠️ Alerts:", results[2].value);
      } else {
        console.error("Alerts failed:", results[2].reason);
        setAlerts(null);
      }

      // Check if everything failed
      if (results.every((r) => r.status === "rejected")) {
        setError("Unable to fetch weather data. Please check your connection.");
      }
    } catch (err: any) {
      console.error("❌ Weather fetch error:", err);
      setError(err.message || "Failed to load weather data");
    }

    setLoading(false);
  }, [city, crop]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const riskColor: Record<string, string> = {
    low: "bg-green-100 text-green-800 border-green-200",
    medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
    high: "bg-orange-100 text-orange-800 border-orange-200",
    critical: "bg-red-100 text-red-800 border-red-200",
  };

  const severityColor: Record<string, string> = {
    low: "bg-green-50 border-green-200",
    medium: "bg-yellow-50 border-yellow-200",
    high: "bg-orange-50 border-orange-200",
    critical: "bg-red-50 border-red-200",
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-2 bg-cyan-100 text-cyan-700 px-4 py-1.5 rounded-full text-sm font-semibold mb-3">
          <Cloud className="w-4 h-4" />
          Weather Intelligence
        </div>
        <h2 className="text-3xl font-extrabold text-gray-800 mb-1">
          Weather & <span className="text-gradient">Crop Impact</span>
        </h2>
        <p className="text-sm text-gray-500 font-medium" style={{ direction: "rtl" }}>
          موسم اور فصل پر اثرات کا تجزیہ
        </p>
      </div>

      {/* Filters */}
      <div className="glass p-4 mb-6 flex flex-wrap gap-3 items-center">
        <select
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className="flex-1 min-w-[160px] p-3 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition"
        >
          {cities.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <select
          value={crop}
          onChange={(e) => setCrop(e.target.value)}
          className="flex-1 min-w-[160px] p-3 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition"
        >
          <option value="wheat">🌾 Wheat / گندم</option>
          <option value="rice">🌾 Rice / چاول</option>
          <option value="cotton">🏵️ Cotton / کپاس</option>
          <option value="sugarcane">🎋 Sugarcane / گنا</option>
          <option value="potato">🥔 Potato / آلو</option>
          <option value="tomato">🍅 Tomato / ٹماٹر</option>
          <option value="maize">🌽 Maize / مکئی</option>
        </select>

        <button
          onClick={fetchData}
          disabled={loading}
          className="p-3 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition disabled:opacity-40"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="glass p-6 mb-6 bg-red-50 border border-red-200 text-center">
          <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <p className="text-sm text-red-600 font-medium">{error}</p>
          <button
            onClick={fetchData}
            className="mt-3 px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 transition"
          >
            Try Again
          </button>
        </div>
      )}

      {loading ? (
        <div className="glass p-16 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto" />
          <p className="text-sm text-gray-400 mt-3">Loading weather data...</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-5 stagger">
          {/* ─── Current Weather ─── */}
          {weather && (
            <div className="glass p-6 stat-glow">
              <h3 className="font-bold mb-4 flex items-center gap-2">
                <Sun className="w-5 h-5 text-yellow-500" />
                Current — {safeString(weather.city, city)}
                {weather.source === "mock" && (
                  <span className="text-[10px] bg-yellow-100 text-yellow-600 px-2 py-0.5 rounded-full font-medium">
                    Demo Data
                  </span>
                )}
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-2xl p-4 text-center border border-red-100/50">
                  <Thermometer className="w-6 h-6 text-red-500 mx-auto mb-1" />
                  <p className="text-3xl font-extrabold text-gray-800">
                    {safeNumber(weather.temperature, 0)}°
                  </p>
                  <p className="text-xs text-gray-400 font-medium">Temperature</p>
                  {weather.feels_like && (
                    <p className="text-[10px] text-gray-400 mt-1">
                      Feels {safeNumber(weather.feels_like)}°
                    </p>
                  )}
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl p-4 text-center border border-blue-100/50">
                  <Droplets className="w-6 h-6 text-blue-500 mx-auto mb-1" />
                  <p className="text-3xl font-extrabold text-gray-800">
                    {safeNumber(weather.humidity, 0)}%
                  </p>
                  <p className="text-xs text-gray-400 font-medium">Humidity</p>
                </div>

                <div className="bg-gradient-to-br from-gray-50 to-slate-50 rounded-2xl p-4 text-center border border-gray-100/50">
                  <Wind className="w-6 h-6 text-gray-500 mx-auto mb-1" />
                  <p className="text-3xl font-extrabold text-gray-800">
                    {safeNumber(weather.wind_speed, 0)}
                  </p>
                  <p className="text-xs text-gray-400 font-medium">Wind m/s</p>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-2xl p-4 text-center border border-purple-100/50">
                  <Cloud className="w-6 h-6 text-purple-400 mx-auto mb-1" />
                  <p className="text-sm font-bold capitalize text-gray-700">
                    {safeString(weather.description, "N/A")}
                  </p>
                  <p className="text-xs text-gray-400 font-medium">Sky</p>
                </div>
              </div>
            </div>
          )}

          {/* ─── Crop Impact ─── */}
          {impact && (
            <div className="glass p-6 stat-glow">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-green-600" />
                  Crop Impact — {safeString(impact.crop, crop)}
                </h3>
                {impact.risk_level && (
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold border ${
                      riskColor[impact.risk_level] || riskColor.medium
                    }`}
                  >
                    {safeString(impact.risk_level, "MEDIUM").toUpperCase()}
                  </span>
                )}
              </div>

              {/* English Analysis */}
              {impact.crop_impact_analysis && (
                <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                  {safeString(impact.crop_impact_analysis)}
                </p>
              )}

              {/* Urdu Analysis */}
              {impact.crop_impact_analysis_urdu && (
                <p
                  className="text-sm text-gray-500 leading-relaxed bg-green-50/50 rounded-xl p-3 border border-green-100/50"
                  style={{ direction: "rtl" }}
                >
                  {safeString(impact.crop_impact_analysis_urdu)}
                </p>
              )}

              {/* Recommended Actions */}
              {(() => {
                const actions = safeStringArray(impact.recommended_actions);
                if (actions.length === 0) return null;
                return (
                  <div className="mt-4 pt-3 border-t border-gray-100">
                    <h4 className="text-xs font-bold text-gray-700 mb-2 uppercase tracking-wider">
                      Recommended Actions
                    </h4>
                    <div className="space-y-1.5">
                      {actions.map((action, i) => (
                        <p
                          key={i}
                          className="text-sm text-gray-600 flex items-start gap-2"
                        >
                          <span className="text-green-500 mt-0.5 shrink-0">✓</span>
                          <span>{action}</span>
                        </p>
                      ))}
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {/* ─── Forecast ─── */}
          {impact?.forecast_7day?.length > 0 && (
            <div className="glass p-6 md:col-span-2 stat-glow">
              <h3 className="font-bold mb-4 flex items-center gap-2">
                <Cloud className="w-5 h-5 text-blue-500" />
                7-Day Forecast — {city}
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-2">
                {impact.forecast_7day.slice(0, 7).map((day: any, i: number) => {
                  const date = day.date ? new Date(day.date) : new Date();
                  const dayName = date.toLocaleDateString("en-US", { weekday: "short" });
                  const dayDate = date.toLocaleDateString("en-US", { month: "short", day: "numeric" });

                  return (
                    <div
                      key={i}
                      className="bg-gradient-to-b from-blue-50/50 to-white rounded-xl p-3 text-center border border-blue-100/30"
                    >
                      <p className="text-[10px] font-bold text-gray-400 uppercase">{dayName}</p>
                      <p className="text-[10px] text-gray-300">{dayDate}</p>
                      <p className="text-lg font-extrabold text-gray-800 my-1">
                        {safeNumber(day.temp, 0)}°
                      </p>
                      <p className="text-[10px] text-gray-400 capitalize truncate">
                        {safeString(day.description, "")}
                      </p>
                      <p className="text-[10px] text-blue-400 mt-1">
                        💧 {safeNumber(day.humidity, 0)}%
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ─── Alerts ─── */}
          {alerts?.alerts && alerts.alerts.length > 0 && (
            <div className="glass p-6 md:col-span-2 stat-glow">
              <h3 className="font-bold mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-500" />
                Weather Alerts
                {alerts.alert_count > 0 && (
                  <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded-full text-[10px] font-bold">
                    {alerts.alert_count} active
                  </span>
                )}
              </h3>
              <div className="space-y-3">
                {alerts.alerts.map((alert: any, i: number) => (
                  <div
                    key={i}
                    className={`p-4 rounded-2xl border fade-in-up ${
                      severityColor[alert.severity] || severityColor.medium
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-sm font-semibold text-gray-800">
                          {safeString(alert.message_en, alert.type)}
                        </p>
                        <p
                          className="text-sm text-gray-600 mt-1"
                          style={{ direction: "rtl" }}
                        >
                          {safeString(alert.message, "")}
                        </p>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold shrink-0 ${
                          riskColor[alert.severity] || ""
                        }`}
                      >
                        {safeString(alert.severity, "").toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No data state */}
          {!weather && !impact && !alerts && !error && (
            <div className="glass p-12 md:col-span-2 text-center">
              <Cloud className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-400 text-sm">No weather data available</p>
              <button
                onClick={fetchData}
                className="mt-3 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-100 transition"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
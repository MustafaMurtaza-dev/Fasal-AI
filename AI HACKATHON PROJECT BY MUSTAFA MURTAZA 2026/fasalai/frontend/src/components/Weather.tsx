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
  Calendar,
  MapPin,
  ArrowRight,
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

const WeatherSkeleton = () => (
  <div className="animate-pulse space-y-6">
    <div className="grid md:grid-cols-2 gap-5">
      <div className="glass h-64 rounded-2xl bg-gray-100/50"></div>
      <div className="glass h-64 rounded-2xl bg-gray-100/50"></div>
      <div className="glass h-48 rounded-2xl bg-gray-100/50 md:col-span-2"></div>
    </div>
  </div>
);

export default function Weather() {
  const [city, setCity] = useState("Lahore");
  const [crop, setCrop] = useState("wheat");
  const [weather, setWeather] = useState<any>(null);
  const [impact, setImpact] = useState<any>(null);
  const [alerts, setAlerts] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const results = await Promise.allSettled([
        weatherAPI.current(city),
        weatherAPI.cropImpact(city, crop),
        weatherAPI.alerts(city, crop),
      ]);

      if (results[0].status === "fulfilled") setWeather(results[0].value);
      else setWeather(null);

      if (results[1].status === "fulfilled") setImpact(results[1].value);
      else setImpact(null);

      if (results[2].status === "fulfilled") setAlerts(results[2].value);
      else setAlerts(null);

      if (results.every((r) => r.status === "rejected")) {
        setError("Unable to fetch weather data. Please check your connection.");
      } else {
        setLastUpdated(new Date());
      }
    } catch (err: any) {
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
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 bg-cyan-100 text-cyan-800 px-4 py-1.5 rounded-full text-sm font-semibold mb-4 shadow-sm">
          <Cloud className="w-4 h-4" />
          Weather Intelligence
        </div>
        <h2 className="text-3xl font-extrabold text-gray-900 mb-2">
          Weather & <span className="text-gradient">Crop Impact</span>
        </h2>
        <p className="text-sm text-gray-500 font-medium" style={{ direction: "rtl" }}>
          موسم اور فصل پر اثرات کا تجزیہ
        </p>
      </div>

      {/* Filters */}
      <div className="glass p-4 mb-8 flex flex-wrap gap-3 items-center shadow-lg shadow-gray-200/50">
        <div className="flex-1 min-w-[200px] relative">
          <MapPin className="absolute left-3 top-3.5 w-4 h-4 text-gray-400" />
          <select
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="w-full pl-10 p-3 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-cyan-500/30 focus:border-cyan-400 transition appearance-none cursor-pointer"
          >
            {cities.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div className="flex-1 min-w-[200px] relative">
          <Sparkles className="absolute left-3 top-3.5 w-4 h-4 text-gray-400" />
          <select
            value={crop}
            onChange={(e) => setCrop(e.target.value)}
            className="w-full pl-10 p-3 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-cyan-500/30 focus:border-cyan-400 transition appearance-none cursor-pointer"
          >
            <option value="wheat">🌾 Wheat / گندم</option>
            <option value="rice">🌾 Rice / چاول</option>
            <option value="cotton">🏵️ Cotton / کپاس</option>
            <option value="sugarcane">🎋 Sugarcane / گنا</option>
            <option value="potato">🥔 Potato / آلو</option>
            <option value="tomato">🍅 Tomato / ٹماٹر</option>
            <option value="maize">🌽 Maize / مکئی</option>
          </select>
        </div>

        <button
          onClick={fetchData}
          disabled={loading}
          className="p-3 bg-cyan-50 text-cyan-600 border border-cyan-100 rounded-xl hover:bg-cyan-100 transition disabled:opacity-40"
          title="Refresh Data"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="glass p-6 mb-6 bg-red-50 border border-red-200 text-center flex flex-col items-center">
          <AlertTriangle className="w-8 h-8 text-red-400 mb-2" />
          <p className="text-sm text-red-600 font-medium mb-3">{error}</p>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-white text-red-600 border border-red-200 rounded-lg text-sm font-medium hover:bg-red-50 transition shadow-sm"
          >
            Try Again
          </button>
        </div>
      )}

      {loading ? (
        <WeatherSkeleton />
      ) : (
        <div className="grid md:grid-cols-2 gap-6 fade-in-up">
          {/* ─── Current Weather ─── */}
          {weather && (
            <div className="glass p-6 md:p-8 stat-glow relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5">
                <Sun className="w-24 h-24 text-yellow-500" />
              </div>

              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="font-bold text-lg text-gray-800 flex items-center gap-2">
                    <Sun className="w-5 h-5 text-yellow-500" />
                    Current Weather
                  </h3>
                  <div className="flex items-center gap-2 mt-1">
                    <MapPin className="w-3 h-3 text-gray-400" />
                    <p className="text-xs text-gray-500 font-medium">{safeString(weather.city, city)}</p>
                    {lastUpdated && (
                      <span className="text-[10px] text-gray-300">• Updated {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    )}
                  </div>
                </div>
                {weather.source === "mock" && (
                  <span className="text-[10px] bg-yellow-100 text-yellow-700 px-2 py-1 rounded-lg font-bold border border-yellow-200">
                    DEMO
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="text-center p-4 rounded-2xl bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-100">
                  <Thermometer className="w-6 h-6 text-orange-500 mx-auto mb-2" />
                  <p className="text-4xl font-black text-gray-800">{safeNumber(weather.temperature, 0)}°</p>
                  <p className="text-xs text-gray-500 font-medium mt-1">Temperature</p>
                  {weather.feels_like && (
                    <p className="text-[10px] text-gray-400 mt-0.5">Feels {safeNumber(weather.feels_like)}°</p>
                  )}
                </div>
                <div className="text-center p-4 rounded-2xl bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-100">
                  <Droplets className="w-6 h-6 text-blue-500 mx-auto mb-2" />
                  <p className="text-4xl font-black text-gray-800">{safeNumber(weather.humidity, 0)}%</p>
                  <p className="text-xs text-gray-500 font-medium mt-1">Humidity</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 border border-gray-100">
                  <div className="p-2 bg-white rounded-lg shadow-sm">
                    <Wind className="w-4 h-4 text-gray-400" />
                  </div>
                  <div>
                    <p className="text-lg font-bold text-gray-700 leading-none">{safeNumber(weather.wind_speed, 0)} <span className="text-xs font-normal text-gray-400">m/s</span></p>
                    <p className="text-[10px] text-gray-400 font-medium">Wind Speed</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 border border-gray-100">
                  <div className="p-2 bg-white rounded-lg shadow-sm">
                    <Cloud className="w-4 h-4 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-gray-700 capitalize leading-tight">{safeString(weather.description, "Clear")}</p>
                    <p className="text-[10px] text-gray-400 font-medium">Conditions</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ─── Crop Impact ─── */}
          {impact && (
            <div className="glass p-6 md:p-8 stat-glow flex flex-col h-full bg-gradient-to-br from-white to-green-50/30">
              <div className="flex justify-between items-start mb-4">
                <h3 className="font-bold text-lg text-gray-800 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-emerald-600" />
                  Crop Analysis
                </h3>
                {impact.risk_level && (
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold border shadow-sm ${riskColor[impact.risk_level] || riskColor.medium
                      }`}
                  >
                    {safeString(impact.risk_level, "MEDIUM").toUpperCase()} RISK
                  </span>
                )}
              </div>

              <div className="flex-1 space-y-4">
                <div className="bg-white/60 p-4 rounded-xl border border-gray-100/50">
                  <p className="text-sm text-gray-700 leading-relaxed font-medium">
                    {safeString(impact.crop_impact_analysis)}
                  </p>
                  {impact.crop_impact_analysis_urdu && (
                    <p
                      className="text-sm text-gray-500 mt-2 leading-relaxed pt-2 border-t border-gray-100"
                      style={{ direction: "rtl" }}
                    >
                      {safeString(impact.crop_impact_analysis_urdu)}
                    </p>
                  )}
                </div>

                {(() => {
                  const actions = safeStringArray(impact.recommended_actions);
                  if (actions.length === 0) return null;
                  return (
                    <div>
                      <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-1">
                        <ArrowRight className="w-3 h-3" /> Recommended Actions
                      </h4>
                      <div className="space-y-2">
                        {actions.map((action, i) => (
                          <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white border border-gray-100 shadow-sm hover:shadow-md hover:border-green-100 transition">
                            <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center shrink-0 mt-0.5">
                              <span className="text-green-600 text-xs font-bold">✓</span>
                            </div>
                            <span className="text-sm text-gray-600 font-medium">{action}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>
          )}

          {/* ─── Forecast ─── */}
          {impact?.forecast_7day?.length > 0 && (
            <div className="glass p-6 md:p-8 md:col-span-2 stat-glow bg-gradient-to-r from-blue-50/20 to-cyan-50/20">
              <h3 className="font-bold mb-6 flex items-center gap-2 text-gray-800">
                <Calendar className="w-5 h-5 text-blue-500" />
                7-Day Forecast — {city}
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3">
                {impact.forecast_7day.slice(0, 7).map((day: any, i: number) => {
                  const date = day.date ? new Date(day.date) : new Date();
                  const dayName = date.toLocaleDateString("en-US", { weekday: "short" });
                  const dayDate = date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
                  const isToday = i === 0;

                  return (
                    <div
                      key={i}
                      className={`rounded-xl p-3 text-center border transition-all ${isToday
                          ? "bg-white border-blue-200 shadow-md transform scale-105 z-10"
                          : "bg-white/60 border-blue-100/50 hover:bg-white hover:border-blue-200 hover:shadow-lg"
                        }`}
                    >
                      <p className={`text-[10px] font-bold uppercase ${isToday ? "text-blue-600" : "text-gray-400"}`}>
                        {isToday ? "Today" : dayName}
                      </p>
                      <p className="text-[10px] text-gray-300 font-medium mt-0.5">{dayDate}</p>
                      <div className="my-2 text-blue-500">
                        {safeNumber(day.temp, 0) > 30 ? <Sun className="w-6 h-6 mx-auto text-orange-400" /> : <Cloud className="w-6 h-6 mx-auto text-blue-300" />}
                      </div>
                      <p className={`text-xl font-black ${isToday ? "text-gray-800" : "text-gray-600"}`}>
                        {safeNumber(day.temp, 0)}°
                      </p>
                      <div className="h-px w-8 bg-gray-100 mx-auto my-2"></div>
                      <p className="text-[10px] text-gray-500 font-medium capitalize truncate">
                        {safeString(day.description, "")}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ─── Alerts ─── */}
          {alerts?.alerts && alerts.alerts.length > 0 && (
            <div className="glass p-6 md:p-8 md:col-span-2 stat-glow bg-red-50/30 border-red-100">
              <h3 className="font-bold mb-4 flex items-center gap-2 text-gray-800">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                Weather Alerts
                {alerts.alert_count > 0 && (
                  <span className="bg-red-100 text-red-600 px-2 py-0.5 rounded-full text-[10px] font-bold border border-red-200">
                    {alerts.alert_count} Active
                  </span>
                )}
              </h3>
              <div className="grid gap-3 sm:grid-cols-2">
                {alerts.alerts.map((alert: any, i: number) => (
                  <div
                    key={i}
                    className={`p-4 rounded-xl border shadow-sm flex gap-3 ${severityColor[alert.severity] || severityColor.medium
                      }`}
                  >
                    <div className="shrink-0 mt-0.5">
                      <AlertTriangle className={`w-5 h-5 ${alert.severity === 'critical' ? 'text-red-500' : 'text-orange-500'
                        }`} />
                    </div>
                    <div>
                      <div className="flex justify-between items-start mb-1">
                        <p className="text-sm font-bold text-gray-800">
                          {safeString(alert.message_en, alert.type)}
                        </p>
                      </div>
                      <p
                        className="text-xs text-gray-600 leading-relaxed font-medium"
                        style={{ direction: "rtl" }}
                      >
                        {safeString(alert.message, "")}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No data state */}
          {!weather && !impact && !alerts && !error && (
            <div className="glass p-12 md:col-span-2 text-center flex flex-col items-center justify-center min-h-[300px]">
              <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mb-4">
                <Cloud className="w-8 h-8 text-blue-300" />
              </div>
              <h3 className="text-lg font-bold text-gray-800 mb-2">Ready for Weather Data</h3>
              <p className="text-gray-400 text-sm max-w-md mx-auto">
                Connect to OpenWeatherMap API in backend settings to see real-time forecast and crop alerts.
              </p>
              <button
                onClick={fetchData}
                className="mt-6 px-6 py-2 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition shadow-lg shadow-blue-600/20"
              >
                Refresh Data
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
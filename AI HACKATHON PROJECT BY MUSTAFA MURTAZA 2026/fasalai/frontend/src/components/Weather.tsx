"use client";
import { useState, useEffect } from "react";
import {
  Cloud,
  Thermometer,
  Droplets,
  Wind,
  Loader2,
  AlertTriangle,
  Sun,
  Sparkles,
} from "lucide-react";
import { weatherAPI } from "@/lib/api";

const cities = [
  "Lahore",
  "Faisalabad",
  "Multan",
  "Karachi",
  "Peshawar",
  "Rawalpindi",
  "Hyderabad",
  "Quetta",
  "Bahawalpur",
  "Sahiwal",
];

export default function Weather() {
  const [city, setCity] = useState("Lahore");
  const [crop, setCrop] = useState("wheat");
  const [weather, setWeather] = useState<any>(null);
  const [impact, setImpact] = useState<any>(null);
  const [alerts, setAlerts] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [w, imp, alt] = await Promise.all([
        weatherAPI.current(city),
        weatherAPI.cropImpact(city, crop),
        weatherAPI.alerts(city, crop),
      ]);
      setWeather(w);
      setImpact(imp);
      setAlerts(alt);
    } catch {}
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [city, crop]);

  const riskColor: Record<string, string> = {
    low: "bg-green-100 text-green-800 border-green-200",
    medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
    high: "bg-orange-100 text-orange-800 border-orange-200",
    critical: "bg-red-100 text-red-800 border-red-200",
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
        <p
          className="text-sm text-gray-500 font-medium"
          style={{ direction: "rtl" }}
        >
          موسم اور فصل پر اثرات کا تجزیہ
        </p>
      </div>

      {/* Filters */}
      <div className="glass p-4 mb-6 flex flex-wrap gap-3">
        <select
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className="flex-1 min-w-[160px] p-3 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition"
        >
          {cities.map((c) => (
            <option key={c}>{c}</option>
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
          <option value="potato">🥔 Potato / آلو</option>
        </select>
      </div>

      {loading ? (
        <div className="glass p-16 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto" />
          <p className="text-sm text-gray-400 mt-3">Loading weather data...</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-5 stagger">
          {/* Current Weather */}
          {weather && (
            <div className="glass p-6 stat-glow">
              <h3 className="font-bold mb-4 flex items-center gap-2">
                <Sun className="w-5 h-5 text-yellow-500" />
                Current — {weather.city}
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-2xl p-4 text-center border border-red-100/50">
                  <Thermometer className="w-6 h-6 text-red-500 mx-auto mb-1" />
                  <p className="text-3xl font-extrabold text-gray-800">
                    {weather.temperature}°
                  </p>
                  <p className="text-xs text-gray-400 font-medium">Temp</p>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl p-4 text-center border border-blue-100/50">
                  <Droplets className="w-6 h-6 text-blue-500 mx-auto mb-1" />
                  <p className="text-3xl font-extrabold text-gray-800">
                    {weather.humidity}%
                  </p>
                  <p className="text-xs text-gray-400 font-medium">Humidity</p>
                </div>
                <div className="bg-gradient-to-br from-gray-50 to-slate-50 rounded-2xl p-4 text-center border border-gray-100/50">
                  <Wind className="w-6 h-6 text-gray-500 mx-auto mb-1" />
                  <p className="text-3xl font-extrabold text-gray-800">
                    {weather.wind_speed}
                  </p>
                  <p className="text-xs text-gray-400 font-medium">
                    Wind m/s
                  </p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-2xl p-4 text-center border border-purple-100/50">
                  <Cloud className="w-6 h-6 text-purple-400 mx-auto mb-1" />
                  <p className="text-sm font-bold capitalize text-gray-700">
                    {weather.description}
                  </p>
                  <p className="text-xs text-gray-400 font-medium">Sky</p>
                </div>
              </div>
            </div>
          )}

          {/* Crop Impact */}
          {impact && (
            <div className="glass p-6 stat-glow">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-green-600" />
                  Crop Impact
                </h3>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold border ${
                    riskColor[impact.risk_level] || ""
                  }`}
                >
                  {impact.risk_level?.toUpperCase()}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                {impact.crop_impact_analysis}
              </p>
              <p
                className="text-sm text-gray-500 leading-relaxed"
                style={{ direction: "rtl" }}
              >
                {impact.crop_impact_analysis_urdu}
              </p>
              {impact.recommended_actions?.length > 0 && (
                <div className="mt-4 pt-3 border-t border-gray-100">
                  <h4 className="text-xs font-bold text-gray-700 mb-2 uppercase tracking-wider">
                    Recommended Actions
                  </h4>
                  <div className="space-y-1.5">
                    {impact.recommended_actions.map(
                      (a: string, i: number) => (
                        <p
                          key={i}
                          className="text-sm text-gray-600 flex items-start gap-2"
                        >
                          <span className="text-green-500 mt-0.5">✓</span>
                          {a}
                        </p>
                      )
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Alerts */}
          {alerts?.alerts?.length > 0 && (
            <div className="glass p-6 md:col-span-2 stat-glow">
              <h3 className="font-bold mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-500" />
                Weather Alerts
              </h3>
              <div className="space-y-3">
                {alerts.alerts.map((a: any, i: number) => (
                  <div
                    key={i}
                    className={`p-4 rounded-2xl border ${
                      a.severity === "critical"
                        ? "bg-red-50 border-red-200"
                        : "bg-yellow-50 border-yellow-200"
                    } fade-in-up`}
                  >
                    <p className="text-sm font-semibold text-gray-800">
                      {a.message_en}
                    </p>
                    <p
                      className="text-sm text-gray-600 mt-1"
                      style={{ direction: "rtl" }}
                    >
                      {a.message}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
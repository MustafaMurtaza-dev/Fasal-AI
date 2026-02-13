"use client";
import { useState, useEffect } from "react";
import {
  CalendarDays,
  Loader2,
  ChevronRight,
  Sparkles,
  MapPin,
  Sprout,
  AlertTriangle,
} from "lucide-react";
import { farmAPI } from "@/lib/api";

const CalendarSkeleton = () => (
  <div className="glass p-6 space-y-4 animate-pulse">
    <div className="h-6 w-48 bg-gray-200 rounded-lg mb-6"></div>
    {[1, 2, 3].map((i) => (
      <div key={i} className="flex gap-4">
        <div className="w-1 bg-gray-200 rounded-full h-24"></div>
        <div className="flex-1 space-y-3 py-2">
          <div className="h-5 w-32 bg-gray-200 rounded-md"></div>
          <div className="h-4 w-full bg-gray-100 rounded-md bg-opacity-60"></div>
          <div className="h-3 w-3/4 bg-gray-100 rounded-md bg-opacity-40"></div>
        </div>
      </div>
    ))}
  </div>
);

export default function Calendar() {
  const [province, setProvince] = useState("punjab");
  const [crop, setCrop] = useState("wheat");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await farmAPI.calendar(province, crop);
      if (!res || !res.calendar || res.calendar.length === 0) {
        throw new Error("No calendar data available for this selection.");
      }
      setData(res);
    } catch (err: any) {
      setError(err?.message || "Failed to load calendar data.");
      setData(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [province, crop]);

  const pColor: Record<string, string> = {
    low: "border-l-green-400 bg-gradient-to-r from-green-50/50 to-transparent",
    medium: "border-l-yellow-400 bg-gradient-to-r from-yellow-50/50 to-transparent",
    high: "border-l-orange-400 bg-gradient-to-r from-orange-50/50 to-transparent",
    critical: "border-l-red-400 bg-gradient-to-r from-red-50/50 to-transparent",
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 bg-violet-100 text-violet-700 px-4 py-1.5 rounded-full text-sm font-semibold mb-4 shadow-sm">
          <CalendarDays className="w-4 h-4" />
          Crop Calendar
        </div>
        <h2 className="text-3xl font-extrabold text-gray-900 mb-2">
          Planting <span className="text-gradient">Schedule</span>
        </h2>
        <p
          className="text-sm text-gray-500 font-medium"
          style={{ direction: "rtl" }}
        >
          صوبائی فصل کیلنڈر اور اہم سرگرمیاں
        </p>
      </div>

      {/* Filters */}
      <div className="glass p-4 mb-8 flex flex-wrap gap-4 items-center justify-center shadow-lg shadow-gray-200/50">
        <div className="relative min-w-[200px]">
          <MapPin className="absolute left-3 top-3.5 w-4 h-4 text-gray-400" />
          <select
            value={province}
            onChange={(e) => setProvince(e.target.value)}
            className="w-full pl-10 p-3 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-violet-500/30 focus:border-violet-400 transition"
          >
            <option value="punjab">🏔️ Punjab</option>
            <option value="sindh">🌊 Sindh</option>
            <option value="kpk">⛰️ KPK</option>
            <option value="balochistan">🏜️ Balochistan</option>
          </select>
        </div>

        <div className="relative min-w-[200px]">
          <Sprout className="absolute left-3 top-3.5 w-4 h-4 text-gray-400" />
          <select
            value={crop}
            onChange={(e) => setCrop(e.target.value)}
            className="w-full pl-10 p-3 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-violet-500/30 focus:border-violet-400 transition"
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
      </div>

      {/* Content */}
      {loading ? (
        <CalendarSkeleton />
      ) : error ? (
        <div className="glass p-12 text-center border-red-100 bg-red-50/30">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-lg font-bold text-gray-800 mb-2">Data Unavailable</h3>
          <p className="text-red-600 mb-6">{error}</p>
          <button
            onClick={fetchData}
            className="px-6 py-2.5 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition shadow-lg shadow-red-600/20"
          >
            Retry
          </button>
        </div>
      ) : data?.calendar?.length > 0 ? (
        <div className="glass p-6 md:p-8 relative overflow-hidden bg-gradient-to-br from-white to-violet-50/30">
          <div className="flex items-center gap-2 mb-6 border-b border-gray-100 pb-4">
            <Sparkles className="w-5 h-5 text-violet-600" />
            <h3 className="font-bold text-lg text-gray-800">
              Annual Activity Timeline
            </h3>
          </div>

          <div className="space-y-4">
            {data.calendar.map((e: any, i: number) => (
              <div
                key={i}
                className={`group border-l-[6px] rounded-r-xl p-5 hover:bg-white hover:shadow-lg transition-all duration-300 relative overflow-hidden ${pColor[e.priority] || pColor.medium
                  }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 mb-2">
                  <span className="text-sm font-black text-gray-800 uppercase tracking-wide min-w-[80px]">
                    {e.month}
                  </span>
                  <div className="hidden sm:block w-px h-4 bg-gray-300"></div>
                  <div className="flex items-center gap-2 flex-1">
                    <span className="text-base font-bold text-violet-700 group-hover:text-violet-800 transition-colors">
                      {e.activity}
                    </span>
                    <ChevronRight className="w-4 h-4 text-violet-300 opacity-0 group-hover:opacity-100 transition-opacity transform group-hover:translate-x-1" />
                  </div>
                </div>

                <div className="ml-0 sm:ml-[108px]">
                  <p
                    className="text-sm text-gray-600 font-medium leading-relaxed mb-1.5"
                    style={{ direction: "rtl" }}
                  >
                    {e.activity_urdu}
                  </p>
                  <p className="text-xs text-gray-500 leading-relaxed bg-white/60 p-2 rounded-lg border border-gray-100/50 group-hover:bg-white/80 transition-colors">
                    {e.details}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="glass p-20 text-center flex flex-col items-center justify-center min-h-[400px]">
          <div className="w-20 h-20 bg-violet-50 rounded-full flex items-center justify-center mb-6">
            <CalendarDays className="w-10 h-10 text-violet-300" />
          </div>
          <h3 className="text-xl font-bold text-gray-800 mb-2">No Schedule Found</h3>
          <p className="text-gray-400">Try selecting a different crop or province.</p>
        </div>
      )}
    </div>
  );
}
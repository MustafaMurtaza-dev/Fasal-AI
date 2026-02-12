"use client";
import { useState, useEffect } from "react";
import {
  CalendarDays,
  Loader2,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { farmAPI } from "@/lib/api";

export default function Calendar() {
  const [province, setProvince] = useState("punjab");
  const [crop, setCrop] = useState("wheat");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      setData(await farmAPI.calendar(province, crop));
    } catch {}
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [province, crop]);

  const pColor: Record<string, string> = {
    low: "border-l-green-400 bg-gradient-to-r from-green-50 to-transparent",
    medium: "border-l-yellow-400 bg-gradient-to-r from-yellow-50 to-transparent",
    high: "border-l-orange-400 bg-gradient-to-r from-orange-50 to-transparent",
    critical: "border-l-red-400 bg-gradient-to-r from-red-50 to-transparent",
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-2 bg-violet-100 text-violet-700 px-4 py-1.5 rounded-full text-sm font-semibold mb-3">
          <CalendarDays className="w-4 h-4" />
          Crop Calendar
        </div>
        <h2 className="text-3xl font-extrabold text-gray-800 mb-1">
          Planting <span className="text-gradient">Schedule</span>
        </h2>
        <p
          className="text-sm text-gray-500 font-medium"
          style={{ direction: "rtl" }}
        >
          صوبائی فصل کیلنڈر
        </p>
      </div>

      {/* Filters */}
      <div className="glass p-4 mb-6 flex gap-3">
        <select
          value={province}
          onChange={(e) => setProvince(e.target.value)}
          className="flex-1 p-3 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-violet-500/30 focus:border-violet-400 transition"
        >
          <option value="punjab">🏔️ Punjab</option>
          <option value="sindh">🌊 Sindh</option>
          <option value="kpk">⛰️ KPK</option>
          <option value="balochistan">🏜️ Balochistan</option>
        </select>
        <select
          value={crop}
          onChange={(e) => setCrop(e.target.value)}
          className="flex-1 p-3 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-violet-500/30 focus:border-violet-400 transition"
        >
          <option value="wheat">🌾 Wheat / گندم</option>
          <option value="rice">🌾 Rice / چاول</option>
          <option value="cotton">🏵️ Cotton / کپاس</option>
          <option value="sugarcane">🎋 Sugarcane / گنا</option>
        </select>
      </div>

      {loading ? (
        <div className="glass p-16 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-violet-500 mx-auto" />
          <p className="text-sm text-gray-400 mt-3">Loading calendar...</p>
        </div>
      ) : data?.calendar?.length > 0 ? (
        <div className="glass p-6">
          <div className="flex items-center gap-2 mb-5">
            <Sparkles className="w-5 h-5 text-violet-600" />
            <h3 className="font-bold text-gray-800">
              Activity Timeline
            </h3>
          </div>
          <div className="space-y-3 stagger">
            {data.calendar.map((e: any, i: number) => (
              <div
                key={i}
                className={`border-l-4 rounded-r-2xl p-4 ${
                  pColor[e.priority] || pColor.medium
                } hover:shadow-md transition-shadow`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-extrabold text-gray-800">
                    {e.month}
                  </span>
                  <ChevronRight className="w-3.5 h-3.5 text-gray-300" />
                  <span className="text-sm font-semibold text-gray-700">
                    {e.activity}
                  </span>
                </div>
                <p
                  className="text-xs text-gray-500 font-medium leading-relaxed"
                  style={{ direction: "rtl" }}
                >
                  {e.activity_urdu}
                </p>
                <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                  {e.details}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="glass p-16 text-center">
          <CalendarDays className="w-12 h-12 text-violet-200 mx-auto mb-3" />
          <p className="text-gray-400">No data available</p>
        </div>
      )}
    </div>
  );
}
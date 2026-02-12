"use client";
import {
  Leaf,
  MessageCircle,
  Camera,
  TrendingUp,
  Cloud,
  CalendarDays,
  Menu,
  X,
  Sparkles,
} from "lucide-react";
import { useState, useEffect } from "react";

const tabs = [
  { id: "home", label: "Home", icon: Leaf },
  { id: "advisory", label: "Advisory", icon: MessageCircle },
  { id: "diagnosis", label: "Diagnosis", icon: Camera },
  { id: "market", label: "Market", icon: TrendingUp },
  { id: "weather", label: "Weather", icon: Cloud },
  { id: "calendar", label: "Calendar", icon: CalendarDays },
];

export default function Navbar({
  active,
  onChange,
}: {
  active: string;
  onChange: (t: any) => void;
}) {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handle = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handle);
    return () => window.removeEventListener("scroll", handle);
  }, []);

  return (
    <nav
      className={`sticky top-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-white/80 backdrop-blur-xl shadow-lg shadow-green-900/5 border-b border-green-100"
          : "bg-white/60 backdrop-blur-md border-b border-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
        {/* Logo */}
        <div
          className="flex items-center gap-2.5 cursor-pointer group"
          onClick={() => onChange("home")}
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-600 to-emerald-500 flex items-center justify-center shadow-lg shadow-green-600/25 group-hover:shadow-green-600/40 transition-shadow">
            <Leaf className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-extrabold text-gradient leading-tight">
              FasalAI
            </span>
            <span className="text-[10px] text-green-600/70 font-medium -mt-0.5 hidden sm:block">
              Smart Agriculture
            </span>
          </div>
        </div>

        {/* Desktop Tabs */}
        <div className="hidden md:flex items-center bg-gray-100/80 rounded-2xl p-1 gap-0.5">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => onChange(t.id)}
              className={`relative flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
                active === t.id
                  ? "bg-white text-green-700 shadow-md shadow-green-900/10"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <t.icon className="w-4 h-4" />
              {t.label}
              {active === t.id && (
                <span className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-green-500" />
              )}
            </button>
          ))}
        </div>

        {/* AI Badge (Desktop) */}
        <div className="hidden md:flex items-center gap-1.5 text-xs font-semibold text-green-700 bg-green-100 px-3 py-1.5 rounded-full">
          <Sparkles className="w-3.5 h-3.5" />
          AI Powered
        </div>

        {/* Mobile Toggle */}
        <button
          className="md:hidden p-2 rounded-xl hover:bg-green-50 transition"
          onClick={() => setOpen(!open)}
        >
          {open ? (
            <X className="w-5 h-5 text-gray-600" />
          ) : (
            <Menu className="w-5 h-5 text-gray-600" />
          )}
        </button>
      </div>

      {/* Mobile Menu */}
      {open && (
        <div className="md:hidden px-4 pb-4 fade-in">
          <div className="bg-white rounded-2xl shadow-xl shadow-green-900/10 p-2 space-y-0.5 border border-green-100">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => {
                  onChange(t.id);
                  setOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left text-sm font-medium transition-all ${
                  active === t.id
                    ? "bg-green-50 text-green-700"
                    : "text-gray-500 hover:bg-gray-50"
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    active === t.id ? "bg-green-600 text-white" : "bg-gray-100"
                  }`}
                >
                  <t.icon className="w-4 h-4" />
                </div>
                {t.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
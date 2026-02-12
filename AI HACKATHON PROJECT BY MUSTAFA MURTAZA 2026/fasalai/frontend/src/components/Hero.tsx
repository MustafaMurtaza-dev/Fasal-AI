"use client";
import { useState, useEffect } from "react";
import {
  Camera,
  MessageCircle,
  TrendingUp,
  Cloud,
  CalendarDays,
  Mic,
  ArrowRight,
  Sparkles,
} from "lucide-react";

const features = [
  {
    id: "diagnosis",
    icon: Camera,
    title: "Disease Diagnosis",
    titleUr: "فصل تشخیص",
    desc: "Upload a photo — AI identifies disease + gives treatment plan",
    color: "from-rose-500 to-orange-500",
    bg: "bg-gradient-to-br from-rose-50 to-orange-50",
  },
  {
    id: "advisory",
    icon: MessageCircle,
    title: "AI Advisory",
    titleUr: "AI مشاورت",
    desc: "Ask any farming question — get expert AI-powered answers",
    color: "from-blue-500 to-indigo-500",
    bg: "bg-gradient-to-br from-blue-50 to-indigo-50",
  },
  {
    id: "market",
    icon: TrendingUp,
    title: "Market Prices",
    titleUr: "منڈی قیمتیں",
    desc: "Real-time prices + AI predictions for best selling time",
    color: "from-emerald-500 to-teal-500",
    bg: "bg-gradient-to-br from-emerald-50 to-teal-50",
  },
  {
    id: "weather",
    icon: Cloud,
    title: "Weather Impact",
    titleUr: "موسم اثر",
    desc: "Weather alerts with crop-specific impact analysis",
    color: "from-cyan-500 to-blue-500",
    bg: "bg-gradient-to-br from-cyan-50 to-blue-50",
  },
  {
    id: "calendar",
    icon: CalendarDays,
    title: "Crop Calendar",
    titleUr: "فصل کیلنڈر",
    desc: "Province-specific planting & harvesting schedules",
    color: "from-violet-500 to-purple-500",
    bg: "bg-gradient-to-br from-violet-50 to-purple-50",
  },
  {
    id: "advisory",
    icon: Mic,
    title: "Urdu Support",
    titleUr: "اردو سپورٹ",
    desc: "Complete bilingual responses — Urdu + English",
    color: "from-amber-500 to-yellow-500",
    bg: "bg-gradient-to-br from-amber-50 to-yellow-50",
  },
];

/* ─── Particle type ─── */
interface Particle {
  left: string;
  animationDuration: string;
  animationDelay: string;
  width: string;
  height: string;
}

export default function Hero({ onNav }: { onNav: (t: any) => void }) {
  /* Generate particles only on client to avoid hydration mismatch */
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    setParticles(
      Array.from({ length: 15 }).map(() => ({
        left: `${Math.random() * 100}%`,
        animationDuration: `${6 + Math.random() * 8}s`,
        animationDelay: `${Math.random() * 5}s`,
        width: `${3 + Math.random() * 6}px`,
        height: `${3 + Math.random() * 6}px`,
      }))
    );
  }, []);

  return (
    <div>
      {/* ─── Hero Section ─── */}
      <section className="gradient-green text-white py-20 md:py-28 px-4 text-center relative">
        {/* Floating Particles — only rendered on client */}
        <div className="hero-particles">
          {particles.map((p, i) => (
            <span
              key={i}
              style={{
                left: p.left,
                animationDuration: p.animationDuration,
                animationDelay: p.animationDelay,
                width: p.width,
                height: p.height,
              }}
            />
          ))}
        </div>

        <div className="relative z-10 max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-white/15 backdrop-blur-sm px-5 py-2 rounded-full mb-6 border border-white/20">
            <Sparkles className="w-4 h-4 text-yellow-300" />
            <span className="text-sm font-medium">
              AI-Powered Smart Agriculture 🌾
            </span>
          </div>

          {/* Title */}
          <h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold mb-4 tracking-tight">
            Fasal
            <span className="text-yellow-300 drop-shadow-[0_2px_10px_rgba(250,204,21,0.3)]">
              AI
            </span>
          </h1>

          {/* Urdu Tagline */}
          <p
            className="text-xl md:text-2xl text-green-100 mb-2 font-medium"
            style={{ direction: "rtl" }}
          >
            پاکستانی کسانوں کا ذہین ساتھی
          </p>

          {/* Subtitle */}
          <p className="text-green-200/80 max-w-2xl mx-auto mb-10 text-base md:text-lg leading-relaxed">
            AI-powered crop disease diagnosis, market predictions & weather
            alerts — in Urdu & English for every farmer
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-wrap justify-center gap-4">
            <button
              onClick={() => onNav("diagnosis")}
              className="group bg-white text-green-800 px-7 py-3.5 rounded-2xl font-bold hover:bg-green-50 transition-all shadow-xl shadow-black/10 flex items-center gap-2.5 text-sm"
            >
              <Camera className="w-5 h-5" />
              Diagnose Disease
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={() => onNav("advisory")}
              className="group bg-white/15 backdrop-blur-sm text-white px-7 py-3.5 rounded-2xl font-bold border border-white/25 hover:bg-white/25 transition-all flex items-center gap-2.5 text-sm"
            >
              <MessageCircle className="w-5 h-5" />
              Ask AI Advisor
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>

        {/* Wave SVG */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg
            viewBox="0 0 1440 80"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M0 32L60 37.3C120 43 240 53 360 56C480 59 600 53 720 45.3C840 37 960 27 1080 26.7C1200 27 1320 37 1380 42.7L1440 48V80H1380C1320 80 1200 80 1080 80C960 80 840 80 720 80C600 80 480 80 360 80C240 80 120 80 60 80H0V32Z"
              fill="#f0fdf4"
            />
          </svg>
        </div>
      </section>

      {/* ─── Features Grid ─── */}
      <section className="py-16 px-4 max-w-6xl mx-auto">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-extrabold text-gray-800 mb-2">
            Powerful Features
          </h2>
          <p className="text-gray-500">
            Everything a Pakistani farmer needs — powered by AI
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5 stagger">
          {features.map((f, i) => (
            <div
              key={i}
              onClick={() => onNav(f.id)}
              className={`${f.bg} p-6 rounded-2xl cursor-pointer hover:shadow-xl hover:-translate-y-1.5 transition-all duration-300 border border-white/60 card-shine group`}
            >
              <div
                className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform duration-300`}
              >
                <f.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-bold text-gray-800 mb-0.5">
                {f.title}
              </h3>
              <p
                className="text-xs text-gray-400 mb-2 font-medium"
                style={{ direction: "rtl" }}
              >
                {f.titleUr}
              </p>
              <p className="text-sm text-gray-600 leading-relaxed">
                {f.desc}
              </p>

              <div className="mt-4 flex items-center gap-1 text-xs font-semibold text-green-600 opacity-0 group-hover:opacity-100 transition-opacity">
                Explore
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
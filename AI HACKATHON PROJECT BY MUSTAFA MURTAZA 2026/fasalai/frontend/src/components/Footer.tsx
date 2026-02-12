import { Leaf, Heart, Github, Sparkles } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-gradient-to-b from-green-900 to-green-950 text-white pt-12 pb-6 mt-16 relative overflow-hidden">
      {/* Decorative Elements */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-green-500/50 to-transparent" />
      <div className="absolute top-0 left-1/4 w-64 h-64 bg-green-800/20 rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-1/4 w-48 h-48 bg-emerald-800/20 rounded-full blur-3xl" />

      <div className="max-w-6xl mx-auto px-4 relative z-10">
        <div className="grid md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-green-600/25">
                <Leaf className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-xl font-extrabold">FasalAI</span>
                <p className="text-xs text-green-400 -mt-0.5">
                  Smart Agriculture
                </p>
              </div>
            </div>
            <p className="text-sm text-green-300/80 leading-relaxed">
              AI-Powered Smart Agriculture Platform for Pakistani Farmers.
              Empowering millions with intelligent farming solutions.
            </p>
          </div>

          {/* Tech Stack */}
          <div>
            <h4 className="font-bold mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-yellow-400" />
              Tech Stack
            </h4>
            <ul className="text-sm text-green-300/80 space-y-1.5">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                Backend: FastAPI + Python
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                AI: GPT-OSS-120B + DeepSeek R1
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                CNN: ResNet50 (33 diseases)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
                Frontend: Next.js + Tailwind CSS
              </li>
            </ul>
          </div>

          {/* AI Features */}
          <div>
            <h4 className="font-bold mb-3 flex items-center gap-2">
              🤖 AI Features
            </h4>
            <ul className="text-sm text-green-300/80 space-y-1.5">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                Multi-Agent Orchestrator
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                In-Memory Knowledge Base
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                Output Validation Pipeline
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-pink-500" />
                Urdu + English Bilingual
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-green-800/50 mt-10 pt-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-1.5 text-sm text-green-400">
              Built with{" "}
              <Heart className="w-4 h-4 text-red-400 animate-pulse" /> for
              Pakistani Farmers
            </div>

            {/* ⭐ Made By Credit */}
            <div className="text-center">
              <p className="text-sm font-semibold text-green-300">
                Made by{" "}
                <span className="text-yellow-400 font-extrabold">
                  Hafiz Mustafa Murtaza
                </span>
              </p>
              <p className="text-xs text-green-500 mt-0.5">
                AI Hackathon 2026
              </p>
            </div>

            <div className="text-xs text-green-600">
              © {new Date().getFullYear()} FasalAI — All rights reserved
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
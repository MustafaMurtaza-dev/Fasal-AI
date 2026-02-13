"use client";
import { useState, useEffect } from "react";
import { Wifi, WifiOff, RefreshCw } from "lucide-react";

export default function BackendStatus() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">(
    "checking"
  );
  const [models, setModels] = useState<Record<string, string>>({});

  const check = async () => {
    setStatus("checking");
    try {
      const url =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const r = await fetch(`${url}/health`, { signal: AbortSignal.timeout(5000) });
      if (r.ok) {
        const d = await r.json();
        setModels(d.models || {});
        setStatus("online");
      } else {
        setStatus("offline");
      }
    } catch {
      setStatus("offline");
    }
  };

  useEffect(() => {
    check();
    const iv = setInterval(check, 30000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div
      className={`fixed bottom-4 right-4 z-50 flex items-center gap-2 px-3.5 py-2 rounded-full text-xs font-semibold shadow-lg border transition-all duration-300 cursor-pointer select-none ${
        status === "online"
          ? "bg-green-50 text-green-700 border-green-200 shadow-green-100"
          : status === "offline"
          ? "bg-red-50 text-red-600 border-red-200 shadow-red-100"
          : "bg-gray-50 text-gray-500 border-gray-200"
      }`}
      onClick={check}
      title={
        status === "online"
          ? `Backend online | ${models.primary || "?"}`
          : "Click to retry"
      }
    >
      {status === "checking" ? (
        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
      ) : status === "online" ? (
        <Wifi className="w-3.5 h-3.5" />
      ) : (
        <WifiOff className="w-3.5 h-3.5" />
      )}
      <span>
        {status === "checking"
          ? "Checking..."
          : status === "online"
          ? "Backend Online"
          : "Backend Offline"}
      </span>
    </div>
  );
}

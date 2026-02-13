"use client";
import { useState, useRef } from "react";
import {
  Camera,
  Loader2,
  Leaf,
  AlertTriangle,
  CheckCircle,
  ImagePlus,
  Sparkles,
  RotateCcw,
  Trash2,
} from "lucide-react";
import { diagnosisAPI } from "@/lib/api";

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export default function Diagnosis() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [crop, setCrop] = useState("");
  const [symptoms, setSymptoms] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [mode, setMode] = useState<"image" | "text">("image");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = (f: File) => {
    if (!f.type.startsWith("image/")) {
      setError("Please select an image file (JPEG, PNG, etc.)");
      return;
    }
    if (f.size > MAX_FILE_SIZE) {
      setError(`Image too large (${(f.size / 1024 / 1024).toFixed(1)}MB). Maximum is 10MB.`);
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError("");
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  };

  const clearAll = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError("");
    setSymptoms("");
    if (fileRef.current) fileRef.current.value = "";
  };

  const diagnoseImage = async () => {
    if (!file) {
      setError("Please select an image first!");
      return;
    }
    setLoading(true);
    setError("");
    try {
      setResult(await diagnosisAPI.uploadImage(file, crop));
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail || err?.message || "Diagnosis failed.";
      setError(`${msg} — Please try again.`);
    }
    setLoading(false);
  };

  const diagnoseText = async () => {
    if (!crop) {
      setError("Please select a crop type!");
      return;
    }
    if (!symptoms.trim()) {
      setError("Please describe the symptoms!");
      return;
    }
    setLoading(true);
    setError("");
    try {
      setResult(await diagnosisAPI.symptoms(crop, symptoms));
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail || err?.message || "Diagnosis failed.";
      setError(`${msg} — Please try again.`);
    }
    setLoading(false);
  };

  const retry = () => {
    if (mode === "image") diagnoseImage();
    else diagnoseText();
  };

  const sevColor: Record<string, string> = {
    low: "bg-green-100 text-green-800 border-green-200",
    medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
    high: "bg-orange-100 text-orange-800 border-orange-200",
    critical: "bg-red-100 text-red-800 border-red-200",
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-2 bg-rose-100 text-rose-700 px-4 py-1.5 rounded-full text-sm font-semibold mb-3">
          <Camera className="w-4 h-4" />
          Disease Diagnosis
        </div>
        <h2 className="text-3xl font-extrabold text-gray-800 mb-1">
          Identify <span className="text-gradient">Crop Disease</span>
        </h2>
        <p
          className="text-sm text-gray-500 font-medium"
          style={{ direction: "rtl" }}
        >
          فصل بیماری تشخیص — تصویر یا علامات سے
        </p>
      </div>

      {/* Mode Selector */}
      <div className="flex justify-center mb-6">
        <div className="flex bg-gray-100 rounded-xl p-1 gap-1">
          <button
            onClick={() => setMode("image")}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${mode === "image"
                ? "bg-white text-green-700 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
              }`}
          >
            <Camera className="w-4 h-4 inline mr-1.5" />
            Image Scan
          </button>
          <button
            onClick={() => setMode("text")}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${mode === "text"
                ? "bg-white text-blue-700 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
              }`}
          >
            <Leaf className="w-4 h-4 inline mr-1.5" />
            Symptoms
          </button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Left: Inputs */}
        <div className="space-y-5">
          {mode === "image" ? (
            /* Upload Zone */
            <div
              className="glass p-2 cursor-pointer group"
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
            >
              {preview ? (
                <div className="relative rounded-2xl overflow-hidden">
                  <img
                    src={preview}
                    alt="Crop"
                    className="w-full h-56 object-cover rounded-2xl"
                  />
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition flex items-center justify-center">
                    <span className="text-white text-sm font-medium opacity-0 group-hover:opacity-100 transition bg-black/50 px-4 py-2 rounded-xl">
                      Change Image
                    </span>
                  </div>
                </div>
              ) : (
                <div className="py-12 border-2 border-dashed border-green-200 rounded-2xl hover:border-green-400 transition bg-green-50/50">
                  <ImagePlus className="w-14 h-14 text-green-300 mx-auto mb-3" />
                  <p className="text-gray-500 font-medium text-sm text-center">
                    Upload crop image
                  </p>
                  <p className="text-gray-400 text-xs mt-1 text-center">
                    Click or drag & drop (max 10MB)
                  </p>
                </div>
              )}
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleInputChange}
              />
            </div>
          ) : (
            /* Symptoms Form */
            <div className="glass p-5 space-y-4">
              <textarea
                value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
                rows={5}
                placeholder="Describe symptoms in detail... / علامات تفصیل سے لکھیں..."
                className="w-full p-3 bg-white border border-gray-200 rounded-xl text-sm outline-none resize-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition placeholder:text-gray-400"
              />
            </div>
          )}

          {/* Crop + Buttons */}
          <div className="glass p-5 space-y-4">
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="w-full p-3 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-400 transition"
            >
              <option value="">Select Crop (optional for image)</option>
              <option value="wheat">Wheat / گندم</option>
              <option value="rice">Rice / چاول</option>
              <option value="cotton">Cotton / کپاس</option>
              <option value="potato">Potato / آلو</option>
              <option value="tomato">Tomato / ٹماٹر</option>
              <option value="maize">Maize / مکئی</option>
              <option value="sugarcane">Sugarcane / گنا</option>
            </select>

            <div className="flex gap-3">
              <button
                onClick={mode === "image" ? diagnoseImage : diagnoseText}
                disabled={loading || (mode === "image" ? !file : !symptoms.trim())}
                className={`flex-1 py-3 rounded-xl font-semibold hover:shadow-lg disabled:opacity-40 transition-all flex items-center justify-center gap-2 text-sm text-white ${mode === "image"
                    ? "bg-gradient-to-r from-green-500 to-emerald-600 hover:shadow-green-600/25"
                    : "bg-gradient-to-r from-blue-500 to-indigo-600 hover:shadow-blue-600/25"
                  }`}
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : mode === "image" ? (
                  <Camera className="w-4 h-4" />
                ) : (
                  <Leaf className="w-4 h-4" />
                )}
                {loading ? "Analyzing..." : "Diagnose"}
              </button>
              {(file || result || symptoms) && (
                <button
                  onClick={clearAll}
                  className="px-4 py-3 rounded-xl font-semibold text-gray-500 bg-gray-100 hover:bg-gray-200 transition-all flex items-center gap-2 text-sm"
                >
                  <Trash2 className="w-4 h-4" />
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 fade-in-scale">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-red-500 shrink-0" />
                <p className="text-sm text-red-700 font-medium flex-1">
                  {error}
                </p>
              </div>
              <button
                onClick={retry}
                disabled={loading}
                className="mt-3 flex items-center gap-1.5 text-xs font-semibold text-red-600 hover:text-red-800 transition"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Retry
              </button>
            </div>
          )}
        </div>

        {/* Right: Results */}
        <div>
          {result ? (
            <div className="glass p-6 space-y-5 fade-in-scale">
              {/* Disease Header */}
              <div className="text-center pb-4 border-b border-gray-100">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center mx-auto mb-3 shadow-lg">
                  <Sparkles className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-extrabold text-gray-800">
                  {result.disease_name || "Analysis Complete"}
                </h3>
                {result.disease_name_urdu && (
                  <p
                    className="text-green-700 font-medium mt-0.5"
                    style={{ direction: "rtl" }}
                  >
                    {result.disease_name_urdu}
                  </p>
                )}
                <div className="flex justify-center gap-3 mt-3 flex-wrap">
                  {result.severity && (
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold border ${sevColor[result.severity] || sevColor.medium
                        }`}
                    >
                      {result.severity.toUpperCase()}
                    </span>
                  )}
                  {result.confidence != null && (
                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200">
                      {(result.confidence * 100).toFixed(0)}% Confidence
                    </span>
                  )}
                </div>
              </div>

              {/* Description */}
              {result.description && (
                <div>
                  <h4 className="font-bold text-sm mb-1.5 flex items-center gap-1.5">
                    Description
                  </h4>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {result.description}
                  </p>
                </div>
              )}

              {/* Treatment Steps */}
              {result.treatment_plan?.length > 0 && (
                <div>
                  <h4 className="font-bold text-sm mb-3 flex items-center gap-1.5">
                    Treatment Plan
                  </h4>
                  <div className="space-y-2.5">
                    {result.treatment_plan.map((s: any, i: number) => (
                      <div
                        key={i}
                        className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-3.5 border border-green-100"
                      >
                        <p className="text-sm font-semibold flex items-center gap-2">
                          <span className="bg-gradient-to-br from-green-500 to-emerald-600 text-white w-6 h-6 rounded-lg inline-flex items-center justify-center text-xs font-bold shadow-sm">
                            {s.step_number}
                          </span>
                          {s.action}
                        </p>
                        {s.action_urdu && (
                          <p
                            className="text-xs text-green-700 mt-1.5 leading-relaxed"
                            style={{ direction: "rtl" }}
                          >
                            {s.action_urdu}
                          </p>
                        )}
                        {s.product_name && (
                          <p className="text-xs text-gray-400 mt-1">
                            Product: {s.product_name} — {s.dosage}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Prevention Tips */}
              {result.prevention_tips?.length > 0 && (
                <div>
                  <h4 className="font-bold text-sm mb-2 flex items-center gap-1.5">
                    Prevention
                  </h4>
                  <div className="space-y-1.5">
                    {result.prevention_tips.map((t: string, i: number) => (
                      <p
                        key={i}
                        className="text-sm text-gray-600 flex items-start gap-2"
                      >
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                        {t}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* New Diagnosis Button */}
              <button
                onClick={clearAll}
                className="w-full py-3 rounded-xl font-semibold text-green-700 bg-green-50 hover:bg-green-100 border border-green-200 transition-all flex items-center justify-center gap-2 text-sm mt-2"
              >
                <RotateCcw className="w-4 h-4" />
                New Diagnosis
              </button>
            </div>
          ) : (
            <div className="glass p-14 text-center">
              <div className="w-20 h-20 rounded-3xl bg-green-50 flex items-center justify-center mx-auto mb-4">
                <Camera className="w-10 h-10 text-green-300" />
              </div>
              <p className="text-gray-400 font-medium">
                {mode === "image"
                  ? "Upload an image to start diagnosis"
                  : "Describe symptoms to get analysis"}
              </p>
              <p
                className="text-gray-400 text-sm mt-1"
                style={{ direction: "rtl" }}
              >
                تصویر اپ لوڈ کریں یا علامات لکھیں
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
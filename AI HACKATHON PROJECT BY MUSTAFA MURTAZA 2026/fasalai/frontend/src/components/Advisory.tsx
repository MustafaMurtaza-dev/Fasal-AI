"use client";
import { useState, useRef, useEffect, Fragment } from "react";
import {
  Send,
  Bot,
  User,
  Loader2,
  Sparkles,
  BookOpen,
  HelpCircle,
} from "lucide-react";
import { advisoryAPI } from "@/lib/api";

/* ─── Types ─── */
interface Msg {
  role: "user" | "bot";
  text: string;
  textUr?: string;
  agents?: string[];
  confidence?: number;
  sources?: string[];
  followUp?: string[];
}

const quickQ = [
  "گندم میں زنگ کا علاج؟",
  "کپاس میں سفید مکھی؟",
  "DAP کتنی ڈالیں؟",
  "آلو کی بجائی کب؟",
  "چاول بلاسٹ علاج؟",
];

/* ═══════════════════════════════════════
   SAFE EXTRACTORS — handles ALL backend formats
   ═══════════════════════════════════════ */

/**
 * Extracts a display string from any value.
 * Handles: string, number, boolean, null, undefined,
 * and objects like SourceReference { source, relevance_score }
 */
function extractDisplayString(item: any): string {
  if (item === null || item === undefined) return "";
  if (typeof item === "string") return item.trim();
  if (typeof item === "number" || typeof item === "boolean") return String(item);

  if (typeof item === "object") {
    // SourceReference: { source: "...", relevance_score: 0.8, excerpt: "..." }
    if (typeof item.source === "string" && item.source.trim()) {
      return item.source.trim();
    }
    // Other common object shapes
    if (typeof item.name === "string" && item.name.trim()) return item.name.trim();
    if (typeof item.title === "string" && item.title.trim()) return item.title.trim();
    if (typeof item.label === "string" && item.label.trim()) return item.label.trim();
    if (typeof item.text === "string" && item.text.trim()) return item.text.trim();
    if (typeof item.value === "string" && item.value.trim()) return item.value.trim();

    // Last resort — stringify but skip empty objects
    try {
      const json = JSON.stringify(item);
      if (json === "{}" || json === "[]") return "";
      return json;
    } catch {
      return "";
    }
  }

  return String(item).trim();
}

/**
 * Converts any array-like value to string[].
 * Filters out empty strings.
 */
function toStringArray(value: any): string[] {
  if (!value) return [];
  if (typeof value === "string") return value.trim() ? [value.trim()] : [];
  if (!Array.isArray(value)) return [];

  const result: string[] = [];
  for (const item of value) {
    const str = extractDisplayString(item);
    if (str.length > 0 && str !== "{}" && str !== "[]" && str !== "null") {
      result.push(str);
    }
  }
  return result;
}

/**
 * Safely extract answer text from API response.
 * Handles cases where answer might be an object or missing.
 */
function extractAnswer(res: any, field: string): string {
  if (!res) return "";
  const val = res[field];
  if (typeof val === "string") return val;
  if (typeof val === "object" && val !== null) {
    // Sometimes LLM returns { answer: { text: "..." } }
    if (typeof val.text === "string") return val.text;
    if (typeof val.content === "string") return val.content;
    try {
      return JSON.stringify(val);
    } catch {
      return "";
    }
  }
  return "";
}

/**
 * Safely extract confidence as a number between 0-1
 */
function extractConfidence(res: any): number | undefined {
  if (!res) return undefined;
  const val = res.confidence;
  if (typeof val === "number" && !isNaN(val)) {
    return Math.min(Math.max(val, 0), 1);
  }
  if (typeof val === "string") {
    const parsed = parseFloat(val);
    if (!isNaN(parsed)) return Math.min(Math.max(parsed, 0), 1);
  }
  return undefined;
}

/* ═══════════════════════════════════════
   MARKDOWN RENDERER
   ═══════════════════════════════════════ */

const HEADING_KEYWORDS = [
  "diagnosis", "treatment plan", "treatment", "recommended varieties",
  "cost estimate", "important notes", "prevention", "prevention tips",
  "suitable crops", "soil test", "fertilizer", "fertilizer recommendations",
  "pest", "pest management", "disease management", "pest & disease",
  "irrigation", "irrigation schedule", "sowing", "sowing schedule",
  "harvest", "harvesting", "calendar", "crop calendar",
  "market", "market analysis", "weather", "weather impact",
  "government support", "next steps", "application tips",
  "cultural measures", "chemical control", "integrated measures",
  "safety", "safety precautions", "useful contacts", "general recommendations",
  "recommended actions", "causes", "symptoms", "identified symptoms",
  "cost", "dosage", "varieties", "notes", "warning", "caution",
  "organic control", "biological control", "summary", "conclusion",
  "additional tips", "storage", "seed treatment", "soil preparation",
  "land preparation", "water management", "nutrient management",
  "weed management", "post-harvest", "marketing tips",
  "تشخیص", "علاج کا منصوبہ", "علاج", "سفارش کردہ اقسام",
  "لاگت کا اندازہ", "اہم نکات", "احتیاط", "روک تھام",
  "مناسب فصلیں", "کھاد", "آبپاشی", "بجائی", "کٹائی",
  "منڈی", "موسم", "حکومتی مدد", "اگلے اقدامات",
  "حفاظتی تدابیر", "مفید رابطے", "عمومی سفارشات",
  "نوٹ", "خوراک", "اقسام", "انتباہ", "خلاصہ",
];

function isHeadingLine(line: string): boolean {
  const trimmed = line.trim();
  if (!trimmed) return false;

  // Already bold: **Heading** or **Heading:**
  if (/^\*\*.+\*\*:?\s*$/.test(trimmed)) return true;

  // Too long
  if (trimmed.length > 80) return false;

  // Ends with sentence punctuation — not a heading
  if (/[.?!]$/.test(trimmed)) return false;

  const lower = trimmed.toLowerCase().replace(/:$/, "").trim();

  // Exact match
  if (HEADING_KEYWORDS.includes(lower)) return true;

  // Partial match for short lines
  for (const kw of HEADING_KEYWORDS) {
    if (lower.includes(kw) && trimmed.length < 50) return true;
  }

  // Title Case detection for 1-6 word lines
  const words = trimmed.split(/\s+/);
  if (words.length >= 1 && words.length <= 6) {
    const sentenceStarters = [
      "the", "a", "an", "if", "when", "do", "it", "this",
      "that", "i", "you", "we", "for", "is", "are", "was",
      "has", "have", "can", "will", "should", "please",
    ];
    if (sentenceStarters.includes(words[0].toLowerCase())) return false;

    const upperCount = words.filter((w) => /^[A-Z\u0600-\u06FF]/.test(w)).length;
    if (upperCount >= Math.ceil(words.length * 0.6) && !trimmed.includes(",")) {
      return true;
    }
  }

  // Standalone Urdu text (short, no period)
  if (/^[\u0600-\u06FF\s:]+$/.test(trimmed) && trimmed.length < 40) {
    return true;
  }

  return false;
}

function extractHeadingText(line: string): string {
  let trimmed = line.trim();
  // Remove ** wrapper
  const boldMatch = trimmed.match(/^\*\*(.*?)\*\*:?\s*$/);
  if (boldMatch) return boldMatch[1];
  // Remove trailing colon
  return trimmed.replace(/:$/, "").trim();
}

function renderInline(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-bold text-gray-900">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

function renderMarkdown(raw: string): React.ReactNode {
  if (!raw || typeof raw !== "string") {
    return <p className="text-[13px] text-gray-500 italic">No content available.</p>;
  }

  const lines = raw.split("\n");
  const elements: React.ReactNode[] = [];
  let paragraph: string[] = [];
  let key = 0;

  const flushParagraph = () => {
    if (paragraph.length === 0) return;
    elements.push(
      <p key={key++} className="text-[13px] leading-relaxed text-gray-700">
        {paragraph.map((l, i) => (
          <Fragment key={i}>
            {renderInline(l)}
            {i < paragraph.length - 1 && <br />}
          </Fragment>
        ))}
      </p>
    );
    paragraph = [];
  };

  for (let idx = 0; idx < lines.length; idx++) {
    const line = lines[idx];
    const trimmed = line.trim();

    if (trimmed === "") {
      flushParagraph();
      continue;
    }

    // ── Markdown headings: # ## ### ──
    const hashMatch = trimmed.match(/^(#{1,4})\s+(.*)/);
    if (hashMatch) {
      flushParagraph();
      elements.push(
        <div key={key++} className="flex items-center gap-2.5 mt-4 mb-2">
          <div className="w-1.5 h-6 rounded-full bg-gradient-to-b from-green-500 to-emerald-600 shadow-sm" />
          <h4 className="text-[14px] font-extrabold text-gray-900 tracking-tight">
            {hashMatch[2].replace(/\*\*/g, "")}
          </h4>
        </div>
      );
      continue;
    }

    // ── Section Heading (keyword based) ──
    if (isHeadingLine(trimmed)) {
      flushParagraph();
      const headingText = extractHeadingText(trimmed);
      elements.push(
        <div key={key++} className="flex items-center gap-2.5 mt-4 mb-2">
          <div className="w-1.5 h-6 rounded-full bg-gradient-to-b from-green-500 to-emerald-600 shadow-sm" />
          <h4 className="text-[14px] font-extrabold text-gray-900 tracking-tight">
            {headingText}
          </h4>
        </div>
      );
      continue;
    }

    // ── Numbered list ──
    const numMatch = trimmed.match(/^(\d+)[.)]\s*(.*)/);
    if (numMatch) {
      flushParagraph();
      elements.push(
        <div
          key={key++}
          className="flex gap-3 items-start bg-gradient-to-r from-green-50/80 to-emerald-50/40 rounded-xl p-3 border border-green-100/60"
        >
          <span className="w-6 h-6 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 text-white flex items-center justify-center text-[11px] font-bold shrink-0 mt-0.5 shadow-sm">
            {numMatch[1]}
          </span>
          <div className="text-[13px] leading-relaxed text-gray-700 flex-1">
            {renderInline(numMatch[2])}
          </div>
        </div>
      );
      continue;
    }

    // ── Bullet list ──
    if (/^[-•✓–]\s/.test(trimmed)) {
      flushParagraph();
      const content = trimmed.replace(/^[-•✓–]\s*/, "");
      elements.push(
        <div key={key++} className="flex gap-2.5 items-start pl-1">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 mt-[9px] shrink-0" />
          <span className="text-[13px] leading-relaxed text-gray-700">
            {renderInline(content)}
          </span>
        </div>
      );
      continue;
    }

    // ── Indented sub-items ──
    if (line.startsWith("  ") || line.startsWith("\t")) {
      const indentedNum = trimmed.match(/^(\d+)[.)]\s*(.*)/);
      if (indentedNum) {
        flushParagraph();
        elements.push(
          <div
            key={key++}
            className="flex gap-3 items-start ml-6 bg-gradient-to-r from-blue-50/60 to-indigo-50/30 rounded-lg p-2.5 border border-blue-100/50"
          >
            <span className="w-5 h-5 rounded-md bg-gradient-to-br from-blue-400 to-indigo-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
              {indentedNum[1]}
            </span>
            <div className="text-[13px] leading-relaxed text-gray-700 flex-1">
              {renderInline(indentedNum[2])}
            </div>
          </div>
        );
        continue;
      }

      if (/^[-•]\s/.test(trimmed)) {
        flushParagraph();
        const content = trimmed.replace(/^[-•]\s*/, "");
        elements.push(
          <div key={key++} className="flex gap-2 items-start ml-6 pl-1">
            <span className="w-1 h-1 rounded-full bg-gray-400 mt-[10px] shrink-0" />
            <span className="text-[12px] leading-relaxed text-gray-600">
              {renderInline(content)}
            </span>
          </div>
        );
        continue;
      }
    }

    // ── Regular text ──
    paragraph.push(trimmed);
  }

  flushParagraph();
  return <div className="space-y-2">{elements}</div>;
}

/* ═══════════════════════════════════════
   BOT MESSAGE BUBBLE
   ═══════════════════════════════════════ */
function BotBubble({
  msg,
  onFollowUp,
}: {
  msg: Msg;
  onFollowUp: (q: string) => void;
}) {
  const [lang, setLang] = useState<"en" | "ur">("en");
  const hasUrdu = !!msg.textUr && msg.textUr.trim().length > 0;
  const displayText = lang === "ur" && hasUrdu ? msg.textUr! : msg.text;

  return (
    <div className="max-w-[88%] fade-in-up">
      {/* Top bar */}
      {(hasUrdu || (msg.confidence != null && msg.confidence > 0)) && (
        <div className="flex items-center gap-2.5 mb-1.5 ml-1">
          {hasUrdu && (
            <div className="flex bg-gray-100 rounded-lg p-0.5">
              <button
                onClick={() => setLang("en")}
                className={`px-2.5 py-1 rounded-md text-[10px] font-bold transition-all ${
                  lang === "en"
                    ? "bg-white text-green-700 shadow-sm"
                    : "text-gray-400 hover:text-gray-600"
                }`}
              >
                English
              </button>
              <button
                onClick={() => setLang("ur")}
                className={`px-2.5 py-1 rounded-md text-[10px] font-bold transition-all ${
                  lang === "ur"
                    ? "bg-white text-green-700 shadow-sm"
                    : "text-gray-400 hover:text-gray-600"
                }`}
              >
                اردو
              </button>
            </div>
          )}
          {msg.confidence != null && msg.confidence > 0 && (
            <div className="flex items-center gap-1.5">
              <div className="w-14 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-green-400 to-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${msg.confidence * 100}%` }}
                />
              </div>
              <span className="text-[10px] text-gray-400 font-medium">
                {(msg.confidence * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      )}

      {/* Message body */}
      <div
        className="bg-white text-gray-800 rounded-2xl rounded-tl-md p-5 shadow-sm border border-gray-100/80"
        style={lang === "ur" ? { direction: "rtl" } : {}}
      >
        {renderMarkdown(displayText)}
      </div>

      {/* Sources */}
      {msg.sources && msg.sources.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2 ml-1">
          {msg.sources.map((s, j) => (
            <span
              key={`src-${j}`}
              className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-medium border border-blue-100 inline-flex items-center gap-1"
            >
              <BookOpen className="w-2.5 h-2.5 shrink-0" />
              {s}
            </span>
          ))}
        </div>
      )}

      {/* Agents */}
      {msg.agents && msg.agents.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-1.5 ml-1">
          {msg.agents.map((a, j) => (
            <span
              key={`agent-${j}`}
              className="text-[10px] bg-green-50 text-green-700 px-2 py-0.5 rounded-full font-semibold border border-green-100"
            >
              ✦ {a}
            </span>
          ))}
        </div>
      )}

      {/* Follow-up Questions */}
      {msg.followUp && msg.followUp.length > 0 && (
        <div className="mt-3 ml-1 space-y-1.5">
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider flex items-center gap-1">
            <HelpCircle className="w-3 h-3" />
            Follow-up Questions
          </p>
          <div className="flex flex-wrap gap-1.5">
            {msg.followUp.map((q, j) => (
              <button
                key={`fq-${j}`}
                onClick={() => onFollowUp(q)}
                className="quick-pill text-[11px] bg-purple-50 text-purple-700 px-3 py-1.5 rounded-xl font-medium hover:bg-purple-100 border border-purple-100/80 text-left"
                style={{ direction: "rtl" }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════
   MAIN ADVISORY COMPONENT
   ═══════════════════════════════════════ */
export default function Advisory() {
  const [msgs, setMsgs] = useState<Msg[]>([
    {
      role: "bot",
      text: "**Assalam-o-Alaikum!** 🌾\n\nI'm **FasalAI** — your AI farming expert for Pakistan.\n\n**I can help with:**\n1. Crop disease identification and treatment\n2. Fertilizer recommendations with dosages\n3. Pest control and spray schedules\n4. Market prices and best selling time\n5. Weather impact on your crops\n\n- Ask in **English**, **Urdu**, or **Roman Urdu**\n- I'll respond in both languages!",
      textUr:
        "**السلام علیکم!** 🌱\n\nمیں **فصل AI** ہوں — پاکستانی کسانوں کا AI زرعی ماہر۔\n\n**میں ان میں مدد کر سکتا ہوں:**\n1. فصل کی بیماری کی تشخیص اور علاج\n2. کھاد کی سفارشات اور مقداریں\n3. کیڑے مار ادویات اور سپرے کا شیڈول\n4. منڈی کی قیمتیں اور فروخت کا بہترین وقت\n5. موسم کا فصل پر اثر\n\n- **انگریزی**، **اردو** یا **رومن اردو** میں پوچھیں\n- دونوں زبانوں میں جواب دوں گا!",
    },
  ]);
  const [input, setInput] = useState("");
  const [crop, setCrop] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);

  const handleFollowUp = (q: string) => {
    setInput(q);
  };

  /* ─── SEND with full debug logging ─── */
  const send = async (overrideInput?: string) => {
    const q = overrideInput || input;
    if (!q.trim() || loading) return;
    setInput("");
    setMsgs((p) => [...p, { role: "user", text: q }]);
    setLoading(true);

    try {
      const res = await advisoryAPI.ask(q, crop || undefined);

      // 🔍 DEBUG: Log what we received
      console.log("📦 Full API response:", res);
      console.log("📝 answer type:", typeof res.answer, "value:", res.answer);
      console.log("📝 answer_urdu type:", typeof res.answer_urdu, "value:", res.answer_urdu);
      console.log("📝 sources type:", typeof res.sources, "value:", res.sources);
      console.log("📝 follow_up type:", typeof res.follow_up_questions, "value:", res.follow_up_questions);
      console.log("📝 agents type:", typeof res.agents_used, "value:", res.agents_used);
      console.log("📝 confidence type:", typeof res.confidence, "value:", res.confidence);

      // Build message with safe extraction
      const answerText = extractAnswer(res, "answer");
      const answerUrdu = extractAnswer(res, "answer_urdu");

      const botMsg: Msg = {
        role: "bot",
        text: answerText || "No response received. Please try again.",
        textUr: answerUrdu || undefined,
        agents: toStringArray(res.agents_used),
        confidence: extractConfidence(res),
        sources: toStringArray(res.sources),
        followUp: toStringArray(res.follow_up_questions),
      };

      // 🔍 DEBUG: Log what we built
      console.log("🤖 Built bot message:", botMsg);

      setMsgs((p) => [...p, botMsg]);
    } catch (err: any) {
      console.error("❌ Send error:", err);
      setMsgs((p) => [
        ...p,
        {
          role: "bot",
          text: `**Error:** ${err.message || "Something went wrong."}\n\nPlease try again.`,
          textUr: "معذرت، غلطی ہوئی۔ دوبارہ کوشش کریں۔",
        },
      ]);
    }
    setLoading(false);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-2 bg-green-100 text-green-700 px-4 py-1.5 rounded-full text-sm font-semibold mb-3">
          <Sparkles className="w-4 h-4" />
          AI Advisory
        </div>
        <h2 className="text-3xl font-extrabold text-gray-800 mb-1">
          Ask Your <span className="text-gradient">Farming Question</span>
        </h2>
        <p
          className="text-sm text-gray-500 font-medium"
          style={{ direction: "rtl" }}
        >
          AI زرعی مشیر — اردو اور انگریزی میں
        </p>
      </div>

      {/* Chat Container */}
      <div className="glass overflow-hidden">
        {/* Crop Selector */}
        <div className="p-4 border-b border-gray-100/80 bg-white/50">
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
              Crop
            </span>
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="flex-1 p-2.5 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-400 transition"
            >
              <option value="">🌿 Any Crop</option>
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

        {/* Messages Area */}
        <div className="h-[500px] overflow-y-auto p-5 space-y-5 bg-gradient-to-b from-green-50/30 to-transparent">
          {msgs.map((m, i) =>
            m.role === "user" ? (
              <div key={i} className="flex gap-3 flex-row-reverse fade-in-up">
                <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0 shadow-md">
                  <User className="w-4 h-4 text-white" />
                </div>
                <div className="max-w-[80%] bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-2xl rounded-tr-md p-4 shadow-md">
                  <p className="text-sm leading-relaxed">{m.text}</p>
                </div>
              </div>
            ) : (
              <div key={i} className="flex gap-3 fade-in-up">
                <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shrink-0 shadow-md pulse-ring">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <BotBubble msg={m} onFollowUp={handleFollowUp} />
              </div>
            )
          )}

          {loading && (
            <div className="flex gap-3 fade-in">
              <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shrink-0 shadow-md">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-white rounded-2xl rounded-tl-md px-5 py-4 border border-gray-100 shadow-sm">
                <div className="typing-dots flex gap-1.5">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {/* Quick Questions */}
        <div className="px-4 py-3 border-t border-gray-100/80 flex gap-2 overflow-x-auto bg-white/40">
          {quickQ.map((q, i) => (
            <button
              key={i}
              onClick={() => {
                setInput(q);
                // Auto-send quick questions
                setTimeout(() => send(q), 100);
              }}
              className="quick-pill shrink-0 text-xs bg-green-50 text-green-700 px-3.5 py-2 rounded-xl font-medium hover:bg-green-100 border border-green-100/80"
              style={{ direction: "rtl" }}
            >
              {q}
            </button>
          ))}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-100/80 bg-white/60">
          <div className="flex gap-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Type your question... / سوال لکھیں..."
              className="flex-1 p-3.5 bg-white border border-gray-200 rounded-2xl text-sm outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-400 transition placeholder:text-gray-400"
            />
            <button
              onClick={() => send()}
              disabled={loading || !input.trim()}
              className="bg-gradient-to-br from-green-500 to-emerald-600 text-white p-3.5 rounded-2xl hover:shadow-lg hover:shadow-green-600/25 disabled:opacity-40 disabled:hover:shadow-none transition-all"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
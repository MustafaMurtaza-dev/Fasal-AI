"use client";
import { useState } from "react";
import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import Advisory from "@/components/Advisory";
import Diagnosis from "@/components/Diagnosis";
import Market from "@/components/Market";
import Weather from "@/components/Weather";
import Calendar from "@/components/Calendar";
import Footer from "@/components/Footer";

type Tab = "home" | "advisory" | "diagnosis" | "market" | "weather" | "calendar";

export default function Home() {
  const [tab, setTab] = useState<Tab>("home");

  return (
    <main className="min-h-screen flex flex-col">
      <Navbar active={tab} onChange={setTab} />

      <div className="flex-1">
        <div key={tab} className="fade-in-up">
          {tab === "home" && <Hero onNav={setTab} />}
          {tab === "advisory" && <Advisory />}
          {tab === "diagnosis" && <Diagnosis />}
          {tab === "market" && <Market />}
          {tab === "weather" && <Weather />}
          {tab === "calendar" && <Calendar />}
        </div>
      </div>

      <Footer />
    </main>
  );
}
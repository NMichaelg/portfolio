"use client";

import { useState } from "react";
import Hero from "@/components/Hero";
import Experience from "@/components/Experience";
import TechStack from "@/components/Techstack";
import Education from "@/components/Education";
import Projects from "@/components/Project";
import Contact from "@/components/Contact";
import ChatWidget from "@/components/ChatWidget";

export default function Home() {
  const [chatOpen, setChatOpen] = useState(false);
  
  return (
    <main>
      <Hero onOpenChat={() => setChatOpen(true)} />
      <Experience />
      <TechStack />
      <Education />
      <Projects />
      <Contact onOpenChat={() => setChatOpen(true)} />
      <ChatWidget open={chatOpen} onOpenChange={setChatOpen} />

    </main>
  );
}

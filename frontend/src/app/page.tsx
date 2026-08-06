import Image from "next/image";
import { Button } from "@/components/ui/button"
import  Hero from "@/components/Hero";
import Experience from "@/components/Experience";
import TechStack from "@/components/Techstack";

export default function Home() {
  return (
    <main>
      <Hero />
      <Experience />
      <TechStack />
    </main>
  );
}

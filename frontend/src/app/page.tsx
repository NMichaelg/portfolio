import Image from "next/image";
import { Button } from "@/components/ui/button"
import  Hero from "@/components/ui/Hero"
import Experience from "@/components/ui/Experience"

export default function Home() {
  return (
    <main>
      <Hero />
      <Experience />
    </main>
  );
}

import Image from "next/image";
import { Button } from "@/components/ui/button"
import  Hero from "@/components/Hero";
import Experience from "@/components/Experience";


export default function Home() {
  return (
    <main>
      <Hero />
      <Experience />
    </main>
  );
}

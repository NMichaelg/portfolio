"use client";

import { useState, useEffect, useRef } from "react";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const LINKS = [
  { id: "experience", label: "Experience" },
  { id: "tech-stack", label: "Tech Stack" },
  { id: "projects", label: "Projects" },
  { id: "education", label: "Education" },
  { id: "contact", label: "Contact" },
];

function scrollToId(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
}

export default function Nav() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const visibleRatios = useRef<Map<string, number>>(new Map());

  useEffect(() => {
    const sections = LINKS.map((l) => document.getElementById(l.id)).filter(
      (el): el is HTMLElement => el !== null
    );

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          visibleRatios.current.set(entry.target.id, entry.intersectionRatio);
        }
        // Pick whichever observed section currently has the greatest visible ratio
        let bestId: string | null = null;
        let bestRatio = 0;
        for (const [id, ratio] of visibleRatios.current) {
          if (ratio > bestRatio) {
            bestRatio = ratio;
            bestId = id;
          }
        }
        if (bestRatio > 0) setActiveId(bestId);
      },
      {
        threshold: [0, 0.25, 0.5, 0.75, 1],
        rootMargin: "-80px 0px -40% 0px", // account for fixed nav height, bias toward upper half of viewport
      }
    );

    sections.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <header className="fixed top-0 inset-x-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="max-w-6xl mx-auto px-6 md:px-16 h-16 flex items-center justify-between">
        <button
          onClick={() => scrollToId("hero")}
          className="font-mono text-sm text-primary tracking-wide"
        >
          Home
        </button>

        <nav className="hidden md:flex items-center gap-1">
          {LINKS.map((link) => (
            <Button
              key={link.id}
              variant="ghost"
              size="sm"
              onClick={() => scrollToId(link.id)}
              className={cn(
                "font-mono text-xs",
                activeId === link.id
                  ? "text-primary bg-muted"
                  : "text-muted-foreground"
              )}
            >
              {link.label}
            </Button>
          ))}
        </nav>

        <button
          className="md:hidden text-foreground"
          onClick={() => setMobileOpen((v) => !v)}
          aria-label="Toggle navigation menu"
        >
          {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </div>

      {mobileOpen && (
        <nav className="md:hidden border-t border-border bg-background/95 backdrop-blur px-6 py-4 flex flex-col gap-1">
          {LINKS.map((link) => (
            <Button
              key={link.id}
              variant="ghost"
              size="sm"
              onClick={() => {
                scrollToId(link.id);
                setMobileOpen(false);
              }}
              className={cn(
                "font-mono text-xs justify-start",
                activeId === link.id
                  ? "text-primary bg-muted"
                  : "text-muted-foreground"
              )}
            >
              {link.label}
            </Button>
          ))}
        </nav>
      )}
    </header>
  );
}
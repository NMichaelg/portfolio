import { Button } from "@/components/ui/button";

export default function Hero({ onOpenChat }: { onOpenChat: () => void }) {
  return (
    <section
      id="hero"
      className="min-h-screen flex items-center px-6 md:px-16 py-24"
    >
      <div className="grid md:grid-cols-2 gap-16 items-center max-w-6xl mx-auto w-full">
        <Left />
        <Right />
      </div>
    </section>
  );
}

export function Left() {
  return (
    <div>
      <h1 className="font-heading font-black text-4xl md:text-6xl leading-[1.05] mb-6">
        I build AI from scratch —
        <br />
        <span className="text-primary">for you.</span>
      </h1>
      <p className="text-muted-foreground text-lg max-w-md mb-8">
        ML/AI/Software Engineer specializing in ML models and AI systems —
        you&apos;re talking to one on this page right now.
      </p>
      <Button size="lg" >
        Talk with my agent
      </Button>
    </div>
  );
}

export function Right() {
  return (
    <div className="flex justify-center">
      <svg
        viewBox="0 0 320 220"
        className="w-full max-w-sm"
        role="img"
        aria-label="Diagram of a router node connecting to a Q and A agent and a deep dive agent"
      >
        {/* connecting lines */}
        <line x1="160" y1="40" x2="80" y2="150" stroke="currentColor" className="text-secondary" strokeWidth="2" />
        <line x1="160" y1="40" x2="240" y2="150" stroke="currentColor" className="text-secondary" strokeWidth="2" />

        {/* router node */}
        <circle cx="160" cy="40" r="28" fill="currentColor" className="text-background" stroke="currentColor" strokeWidth="2" />
        <circle cx="160" cy="40" r="28" fill="none" stroke="currentColor" className="text-primary" strokeWidth="2" />
        <text x="160" y="45" textAnchor="middle" className="fill-foreground font-mono" fontSize="10">
          router
        </text>

        {/* qa_agent node */}
        <circle cx="80" cy="150" r="28" fill="currentColor" className="text-background" />
        <circle cx="80" cy="150" r="28" fill="none" stroke="currentColor" className="text-secondary" strokeWidth="2" />
        <text x="80" y="155" textAnchor="middle" className="fill-foreground font-mono" fontSize="9">
          qa_agent
        </text>

        {/* deep_dive_agent node */}
        <circle cx="240" cy="150" r="28" fill="currentColor" className="text-background" />
        <circle cx="240" cy="150" r="28" fill="none" stroke="currentColor" className="text-secondary" strokeWidth="2" />
        <text x="240" y="152" textAnchor="middle" className="fill-foreground font-mono" fontSize="8">
          deep_dive
        </text>
      </svg>
    </div>
  );
}
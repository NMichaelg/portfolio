type Role = {
  title: string;
  org: string;
  period: string;
  bullets: string[];
};

const roles: Role[] = [
  {
    title: "SAP System Administrator",
    org: "Homelab — michaelprivate.servebeer.com",
    period: "Aug 2025 — Present",
    bullets: [
      "Designed and built a 24/7 self-hosted homelab: cloud storage, media streaming, adblocking",
      "Provisioned lightweight Linux on Raspberry Pi 5",
      "Configured network segmentation and private VPNs for secure access",
      "Maintained uptime and reproducibility with Docker",
    ],
  },
  {
    title: "AI Software Engineer",
    org: "IVS Joint Stock Company",
    period: "Jun 2025 — Nov 2025",
    bullets: [
      "Built multi-agent AI systems with LangGraph, LangChain, and n8n",
      "Integrated and optimized local LLMs with Ollama",
      "Shipped scalable, low-latency endpoints with FastAPI",
    ],
  },
  {
    title: "AI Engineer",
    org: "IVS Joint Stock Company",
    period: "Jun 2024 — Sep 2024",
    bullets: [
      "Contributed to AI research and proof-of-concept features for enterprise applications",
    ],
  },
  {
    title: "Working Student",
    org: "Unlimited Research Group of AI (URA), HCMUT",
    period: "Jul 2023 — Jun 2024",
    bullets: [
      "Researched deep learning architectures and foundational model applications",
    ],
  },
];

export default function Experience() {
  return (
    <section id="experience" className="px-6 md:px-16 py-20 md:py-28">
      <div className="max-w-3xl mx-auto">
        <p className="font-mono text-sm text-primary tracking-wide mb-3">
          EXPERIENCE
        </p>
        <h2 className="font-heading font-black text-3xl md:text-4xl mb-12">
          Where I&apos;ve built things.
        </h2>

        <div className="space-y-10">
          {roles.map((role) => (
            <div
              key={role.title + role.period}
              className="border-l-2 border-secondary pl-6 relative"
            >
              <span className="absolute -left-[7px] top-1 w-3 h-3 rounded-full bg-primary" />
              <p className="font-mono text-xs text-muted-foreground mb-1">{role.period}</p>
              <h3 className="font-heading font-black text-xl mb-1">
                {role.title}
              </h3>
              <p className="font-mono text-sm text-secondary mb-3">{role.org}</p>
              <ul className="space-y-1.5 text-foreground/90 text-sm md:text-base">
                {role.bullets.map((b) => (
                  <li key={b} className="flex gap-2">
                    <span className="text-primary shrink-0">—</span>
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
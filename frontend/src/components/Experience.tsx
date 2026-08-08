import type { ExperienceRole } from "@/lib/content";

export default function Experience({ roles }: { roles: ExperienceRole[] }) {
  return (
    <section id="experience" className="border-t border-border px-6 md:px-16 py-20 md:py-28">
      <div className="max-w-3xl mx-auto">
        <p className="font-mono text-sm text-primary tracking-wide mb-3">EXPERIENCE</p>
        <h2 className="font-heading font-black text-3xl md:text-4xl mb-12">Where I&apos;ve built things.</h2>
        <div className="space-y-10">
          {roles.map((role) => (
            <div key={role.title + role.period} className="border-l-2 border-secondary pl-6 relative">
              <span className="absolute -left-1.75 top-1 w-3 h-3 rounded-full bg-primary" />
              <p className="font-mono text-xs text-muted-foreground mb-1">{role.period}</p>
              <h3 className="font-heading font-black text-xl mb-1">{role.title}</h3>
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
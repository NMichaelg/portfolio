import { Badge } from "@/components/ui/badge";
import type { EducationData } from "@/lib/content";

export default function Education({ data }: { data: EducationData }) {
  return (
    <section id="education" className="border-t border-border px-6 md:px-16 py-20 md:py-28">
      <div className="max-w-3xl mx-auto">
        <p className="font-mono text-sm text-primary tracking-wide mb-3">EDUCATION</p>
        <h2 className="font-heading font-black text-3xl md:text-4xl mb-12">Where I studied.</h2>
        <div className="space-y-10 mb-12">
          {data.degrees.map((degree) => (
            <div key={degree.title} className="border-l-2 border-secondary pl-6 relative">
              <span className="absolute -left-1.75 top-1 w-3 h-3 rounded-full bg-primary" />
              <p className="font-mono text-xs text-muted-foreground mb-1">{degree.period}</p>
              <h3 className="font-heading font-black text-xl mb-1">{degree.title}</h3>
              <p className="font-mono text-sm text-secondary">
                {degree.org}
                {degree.note && <span className="block text-xs mt-0.5 text-muted-foreground">{degree.note}</span>}
              </p>
            </div>
          ))}
        </div>
        <div className="grid sm:grid-cols-2 gap-8">
          <div>
            <h3 className="font-mono text-sm text-muted-foreground mb-3">Honors & Awards</h3>
            <div className="flex flex-wrap gap-2">
              {data.honors.map((h) => <Badge key={h} variant="secondary">{h}</Badge>)}
            </div>
          </div>
          <div>
            <h3 className="font-mono text-sm text-muted-foreground mb-3">Certifications</h3>
            <div className="flex flex-wrap gap-2">
              {data.certifications.map((c) => <Badge key={c} variant="secondary">{c}</Badge>)}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
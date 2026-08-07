import { Badge } from "@/components/ui/badge";

type Degree = {
  title: string;
  org: string;
  period: string;
  note?: string;
};

const degrees: Degree[] = [
  {
    title: "Bachelor of Engineering, Computer Science",
    org: "Bach Khoa University (HCMUT)",
    period: "Aug 2020 — Jun 2025",
    note: "Ho Chi Minh City, Vietnam",
  },
  {
    title: "High School Diploma",
    org: "Lương Thế Vinh High School",
    period: "2017 — 2020",
  },
];

const honors = [
  "Gold Medal — National Contest of Creativity for Teenagers (2020)",
  "National Creative Youth Medal",
  "Gold Medal — State Contest of Science and Engineering",
];

const certifications = ["IELTS 7.0"];

export default function Education() {
  return (
    <section id="education" className="border-t border-border px-6 md:px-16 py-20 md:py-28">
      <div className="max-w-3xl mx-auto">
        <p className="font-mono text-sm text-primary tracking-wide mb-3">
          EDUCATION
        </p>
        <h2 className="font-heading font-black text-3xl md:text-4xl mb-12">
          Where I studied.
        </h2>

        <div className="divide-y divide-border mb-12">
          {degrees.map((degree) => (
            <div
              key={degree.title}
              className="py-6 flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1"
            >
              <div>
                <h3 className="font-heading font-black text-xl">
                  {degree.title}
                </h3>
                <p className="font-mono text-sm text-secondary">
                  {degree.org}
                  {degree.note && (
                    <span className="text-muted-foreground"> · {degree.note}</span>
                  )}
                </p>
              </div>
              <p className="font-mono text-sm text-muted-foreground shrink-0">
                {degree.period}
              </p>
            </div>
          ))}
        </div>
        {/* honors/certifications badges unchanged below */}
      </div>
    </section>
  );
}
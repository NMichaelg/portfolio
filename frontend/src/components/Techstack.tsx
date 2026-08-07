import { Badge } from "@/components/ui/badge";

type Group = {
  label: string;
  skills: string[];
};

const groups: Group[] = [
  {
    label: "AI & Agentic Workflows",
    skills: [
      "LangGraph",
      "LangChain",
      "n8n",
      "Ollama",
      "Local LLMs",
      "AI Agents",
      "Prompt Engineering",
    ],
  },
  {
    label: "Backend & APIs",
    skills: ["FastAPI", "Python", "RESTful API Design"],
  },
  {
    label: "Infrastructure & DevOps",
    skills: [
      "Linux",
      "Raspberry Pi 5",
      "Docker",
      "Network Segmentation",
      "Private VPNs",
      "Cloud Storage",
    ],
  },
  {
    label: "Traditional IT & Enterprise",
    skills: [
      "SAP Implementation",
      "System Administration",
      "Quality Assurance",
      "Project Management",
    ],
  },
];

export default function TechStack() {
  return (
    <section id="tech-stack" className="border-t border-border px-6 md:px-16 py-20 md:py-28">
      <div className="max-w-3xl mx-auto">
        <p className="font-mono text-sm text-primary tracking-wide mb-3">
          TECH STACK
        </p>
        <h2 className="font-heading font-black text-3xl md:text-4xl mb-12">
          What I build with.
        </h2>

        <div className="space-y-8">
          {groups.map((group) => (
            <div key={group.label}>
              <h3 className="font-mono text-sm text-muted-foreground mb-3">
                {group.label}
              </h3>
              <div className="flex flex-wrap gap-2">
                {group.skills.map((skill) => (
                  <Badge key={skill} variant="secondary">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
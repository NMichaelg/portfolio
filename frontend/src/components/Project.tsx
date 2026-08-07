import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";


export type Project = {
  name: string;
  description: string;
  tags: string[];
  url: string;
};

// TODO: replace with real projects
export const projects: Project[] = [
  {
    name: "portfolio-agent",
    description:
      "This site — a LangGraph multi-agent chatbot backed by FastAPI, streaming NDJSON to a Next.js frontend.",
    tags: ["LangGraph", "FastAPI", "Next.js"],
    url: "https://github.com/yourusername/portfolio-agent",
  },
  {
    name: "sample-project-two",
    description: "Placeholder description — swap in a real project.",
    tags: ["Python", "Docker"],
    url: "https://github.com/yourusername/sample-project-two",
  },
  {
    name: "sample-project-three",
    description: "Placeholder description — swap in a real project.",
    tags: ["FastAPI", "PostgreSQL"],
    url: "https://github.com/yourusername/sample-project-three",
  },
];



export default function Projects() {
  return (
    <section id="projects" className="border-t border-border px-6 md:px-16 py-20 md:py-28">
      <div className="max-w-3xl mx-auto">
        <p className="font-mono text-sm text-primary tracking-wide mb-3">
          PROJECTS
        </p>
        <h2 className="font-heading font-black text-3xl md:text-4xl mb-12">
          What I&apos;ve shipped.
        </h2>

        <div className="grid sm:grid-cols-2 gap-4">
          {projects.map((project) => (
            <  a
              key={project.name}
              href={project.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block"
            >
              <Card className="h-full hover:border-primary transition-colors">
                <CardHeader>
                  <CardTitle className="font-mono text-base">
                    {project.name}
                  </CardTitle>
                  <CardDescription>{project.description}</CardDescription>
                </CardHeader>
                <CardFooter className="flex flex-wrap gap-2">
                  {project.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </CardFooter>
              </Card>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
import { Card, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getRoleColorClass } from "@/lib/roleColors";
import type { Project } from "@/lib/content";

export default function Projects({ projects }: { projects: Project[] }) {
  return (
    <section id="projects" className="border-t border-border px-6 md:px-16 py-20 md:py-28">
      <div className="max-w-3xl mx-auto">
        <p className="font-mono text-sm text-primary tracking-wide mb-3">PROJECTS</p>
        <h2 className="font-heading font-black text-3xl md:text-4xl mb-12">What I&apos;ve shipped.</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {projects.map((project) => (
            <a key={project.name} href={project.url} target="_blank" rel="noopener noreferrer" className="block">
              <Card className="h-full hover:border-primary transition-colors">
                <CardHeader>
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {project.role.map((r) => (
                      <span
                        key={r}
                        className={`text-xs font-mono px-2 py-0.5 rounded-full border ${getRoleColorClass(r)}`}
                      >
                        {r}
                      </span>
                    ))}
                  </div>
                  <CardTitle className="font-mono text-base">{project.name}</CardTitle>
                  <ul className="flex flex-col gap-1.5 text-muted-foreground text-sm mt-1">
                    {project.description.map((line) => (
                      <li key={line} className="flex items-center gap-2">
                        <span className="w-1 h-1 rounded-full bg-primary shrink-0" />
                        <span>{line}</span>
                      </li>
                    ))}
                  </ul>
                </CardHeader>
                <CardFooter className="flex flex-wrap gap-2">
                  {project.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">{tag}</Badge>
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
import { Card, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
                  <CardTitle className="font-mono text-base">{project.name}</CardTitle>
                  <CardDescription>{project.description}</CardDescription>
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
"use client";

import { useState, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getRoleColorClass } from "@/lib/roleColors";
import { cn } from "@/lib/utils";
import type { Project } from "@/lib/content";

export default function Projects({ projects }: { projects: Project[] }) {
  const [selectedRole, setSelectedRole] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  const allRoles = useMemo(
    () => Array.from(new Set(projects.flatMap((p) => p.role))),
    [projects]
  );
  const allTags = useMemo(
    () => Array.from(new Set(projects.flatMap((p) => p.tags))),
    [projects]
  );

  const filtered = projects.filter(
    (p) =>
      (!selectedRole || p.role.includes(selectedRole)) &&
      (!selectedTag || p.tags.includes(selectedTag))
  );

  const hasActiveFilter = selectedRole !== null || selectedTag !== null;

  return (
    <section id="projects" className="border-t border-border px-6 md:px-16 py-20 md:py-28">
      <div className="max-w-3xl mx-auto">
        <p className="font-mono text-sm text-primary tracking-wide mb-3">PROJECTS</p>
        <h2 className="font-heading font-black text-3xl md:text-4xl mb-8">What I&apos;ve shipped.</h2>

        {/* Role filter */}
        <div className="flex flex-wrap items-center gap-1.5 mb-2">
          <span className="font-mono text-xs text-muted-foreground mr-1">Role:</span>
          {allRoles.map((role) => (
            <button
              key={role}
              onClick={() => setSelectedRole(selectedRole === role ? null : role)}
              className={cn(
                "text-xs font-mono px-2 py-0.5 rounded-full border transition-all",
                getRoleColorClass(role),
                selectedRole === role
                  ? "ring-2 ring-offset-1 ring-offset-background ring-current"
                  : "opacity-60 hover:opacity-100"
              )}
            >
              {role}
            </button>
          ))}
        </div>

        {/* Tag filter */}
        <div className="flex flex-wrap items-center gap-1.5 mb-6">
          <span className="font-mono text-xs text-muted-foreground mr-1">Tag:</span>
          {allTags.map((tag) => (
            <button key={tag} onClick={() => setSelectedTag(selectedTag === tag ? null : tag)}>
              <Badge
                variant={selectedTag === tag ? "default" : "secondary"}
                className="cursor-pointer"
              >
                {tag}
              </Badge>
            </button>
          ))}
        </div>

        {hasActiveFilter && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setSelectedRole(null);
              setSelectedTag(null);
            }}
            className="font-mono text-xs mb-6 -mt-2"
          >
            Clear filters ✕
          </Button>
        )}

        {filtered.length === 0 ? (
          <p className="text-muted-foreground text-sm">No projects match these filters.</p>
        ) : (
          <div className="grid sm:grid-cols-2 gap-4">
            {filtered.map((project) => (
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
        )}
      </div>
    </section>
  );
}
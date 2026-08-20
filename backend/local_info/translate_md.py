#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

# Set this to your name, or add a "name" field under site.json's "hero" or
# top-level and read it from there instead.
BASE_BACKEND_DIR = Path(__file__).parent.parent
DEFAULT_NAME = ""
INPUT_PATH = BASE_BACKEND_DIR/'local_info'/"content.json"
OUTPUT_PATH = BASE_BACKEND_DIR/'local_info'/"content.md"

def _render_contact(contact: dict) -> str:
    lines = ["## Contact Information"]

    for key, value in contact.items():
        if value:
            label = key.replace("_", " ").title()
            lines.append(f"- **{label}:** {value}")

    return "\n".join(lines)


def _render_summary(hero: dict) -> str:
    lines = ["## Professional Summary"]
    if subhead := hero.get("subhead"):
        lines.append(subhead)
    return "\n".join(lines) if len(lines) > 1 else ""


def _render_skills(tech_stack: list) -> str:
    if not tech_stack:
        return ""
    lines = ["## Core Technical Skills", ""]
    for category in tech_stack:
        label = category.get("label", "")
        skills = ", ".join(category.get("skills", []))
        if label and skills:
            lines.append(f"* **{label}:** {skills}.")
    return "\n".join(lines)


def _render_experience(experience: list) -> str:
    if not experience:
        return ""
    lines = ["## Professional Experience", ""]
    for job in experience:
        title = job.get("title", "")
        org = job.get("org", "")
        period = job.get("period", "")
        lines.append(f"### {title}")
        lines.append(f"**{org}** | *{period}*")
        for bullet in job.get("bullets", []):
            lines.append(f"* {bullet}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _render_projects(projects: list) -> str:
    if not projects:
        return ""

    lines = ["## Projects", ""]

    for project in projects:
        lines.append(f"### {project.get('name', '')}")

        roles = ", ".join(project.get("role", []))
        if roles:
            lines.append(f"**Role:** {roles}")

        for description in project.get("description", []):
            lines.append(f"- {description}")

        if project.get("tags"):
            lines.append(f"**Tech:** {', '.join(project['tags'])}")

        if project.get("url"):
            lines.append(f"[View Project]({project['url']})")

        lines.append("")

    return "\n".join(lines).rstrip()


def _render_education(education: dict) -> str:
    if not education:
        return ""
    out_parts = []

    degrees = education.get("degrees", [])
    if degrees:
        lines = ["## Education", ""]
        for degree in degrees:
            title = degree.get("title", "")
            org = degree.get("org", "")
            period = degree.get("period", "")
            note = degree.get("note", "")
            lines.append(f"### {title}")
            lines.append(f"**{org}** | *{period}*")
            if note:
                lines.append(f"* *Location:* {note}")
            lines.append("")
        out_parts.append("\n".join(lines).rstrip())

    certs = education.get("certifications", [])
    if certs:
        out_parts.append("## Certifications\n" + "\n".join(f"* {c}" for c in certs))

    honors = education.get("honors", [])
    if honors:
        out_parts.append("## Honors & Awards\n" + "\n".join(f"* {h}" for h in honors))

    return "\n\n---\n\n".join(out_parts)


def _render_languages(languages: dict) -> str:
    if not languages:
        return ""
    lines = ["## Languages"]
    for lang, level in languages.items():
        lines.append(f"* **{lang}:** {level}")
    return "\n".join(lines)


def _generate_markdown(data: dict, name: str = DEFAULT_NAME) -> str:
    sections = [
        f"# Portfolio Knowledge Base",
        _render_summary(data.get("hero", {})),
        _render_experience(data.get("experience", [])),
        _render_skills(data.get("techStack", [])),
        _render_projects(data.get("projects", [])),
        _render_education(data.get("education", {})),
        _render_languages(data.get("languages", {})),
        _render_contact(data.get("contact", {})),
    ]
    return "\n\n---\n\n".join(s for s in sections if s.strip()) + "\n"


def generate_markdown_file():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=INPUT_PATH,
        help="Path to site.json, relative to this script (default: content.json)",
    )
    parser.add_argument(
        "--output",
        default=OUTPUT_PATH,
        help="Path to write generated markdown, relative to this script (default: content.md)",
    )
    parser.add_argument("--name", default=DEFAULT_NAME, help="Name for the H1 title")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    input_path = (Path(args.input) if parser.get_default("input") != args.input
                  else script_dir / args.input).resolve()
    output_path = (Path(args.output) if parser.get_default("output") != args.output
                   else script_dir / args.output).resolve()

    data = json.loads(input_path.read_text(encoding="utf-8"))
    markdown = _generate_markdown(data, name=args.name)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Generated {output_path} from {input_path}")

if __name__ == "__main__":
    generate_markdown_file()
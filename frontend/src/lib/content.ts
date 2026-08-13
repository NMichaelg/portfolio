export type HeroData = {
  eyebrow: string;
  heading: string;
  subhead: string;
};

export type ExperienceRole = {
  title: string;
  org: string;
  period: string;
  bullets: string[];
};

export type TechGroup = {
  label: string;
  skills: string[];
};

export type Project = {
  name: string;
  description: string;
  tags: string[];
  url: string;
};

export type Degree = {
  title: string;
  org: string;
  period: string;
  note?: string;
};

export type EducationData = {
  degrees: Degree[];
  honors: string[];
  certifications: string[];
};

export type ContactData = {
  email: string;
  linkedin: string;
  facebook: string;
};

export type SiteContent = {
  hero: HeroData;
  experience: ExperienceRole[];
  techStack: TechGroup[];
  projects: Project[];
  education: EducationData;
  contact: ContactData;
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getSiteContent(): Promise<SiteContent> {
  const res = await fetch(`${API_BASE}/api/content`, {
    next: { revalidate: 3600 }, // re-fetch at most once per hour
  });

  if (!res.ok) {
    throw new Error(`Failed to load site content (${res.status})`);
  }

  return res.json();
}
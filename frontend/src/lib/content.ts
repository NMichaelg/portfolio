import siteContent from "../../contents/site.json";

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

export function getSiteContent(): SiteContent {
  return siteContent as SiteContent;
}
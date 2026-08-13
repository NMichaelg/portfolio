import { getSiteContent } from "@/lib/content";
import { ChatProvider } from "@/components/ChatProvider";
import Hero from "@/components/Hero";
import Experience from "@/components/Experience";
import TechStack from "@/components/TechStack";
import Projects from "@/components/Projects";
import Education from "@/components/Education";
import Contact from "@/components/Contact";
import ChatWidget from "@/components/ChatWidget";

export default async function Home() {
  const content = await getSiteContent();

  return (
    <ChatProvider>
      <main>
        <Hero data={content.hero} />
        <Experience roles={content.experience} />
        <TechStack groups={content.techStack} />
        <Projects projects={content.projects} />
        <Education data={content.education} />
        <Contact data={content.contact} />
        <ChatWidget />
      </main>
    </ChatProvider>
  );
}
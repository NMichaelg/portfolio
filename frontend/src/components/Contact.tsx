import ChatTriggerButton from "@/components/ChatTriggerButton";
import type { ContactData } from "@/lib/content";

export default function Contact({ data }: { data: ContactData }) {
  return (
    <section id="contact" className="border-t border-border px-6 md:px-16 py-32 md:py-40">
      <div className="max-w-3xl mx-auto text-center">
        <h2 className="font-heading font-black text-4xl md:text-6xl leading-tight mb-4">Let&apos;s talk.</h2>
        <p className="font-mono text-sm text-secondary mb-2">
          From the matrix equations to the agent chat box — I&apos;m the one in charge.
        </p>
        <p className="text-muted-foreground text-lg mb-10">Ask my assistant for my CV, or reach me directly.</p>

        <ChatTriggerButton size="lg" className="mb-10">Ask my AI</ChatTriggerButton>

        <div className="flex flex-wrap justify-center gap-x-6 gap-y-2 font-mono text-sm text-muted-foreground mb-16">
          <a href={`mailto:${data.email}`} className="hover:text-primary transition-colors">{data.email}</a>
          <a href={data.linkedin} target="_blank" rel="noopener noreferrer" className="hover:text-primary transition-colors">LinkedIn</a>
          <a href={data.facebook} target="_blank" rel="noopener noreferrer" className="hover:text-primary transition-colors">Facebook</a>
        </div>

        <p className="font-mono text-xs text-muted-foreground/60">
          Ho Chi Minh City, Vietnam · Q{Math.floor(new Date().getMonth() / 3) + 1} {new Date().getFullYear()}
        </p>
      </div>
    </section>
  );
}
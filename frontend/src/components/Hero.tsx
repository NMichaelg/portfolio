import ChatTriggerButton from "@/components/ChatTriggerButton";
import type { HeroData } from "@/lib/content";



export default function Hero({ data }: { data: HeroData }) {
  return (
    <section id="hero" className="min-h-screen flex items-center px-6 md:px-16 py-24">
      <div className="grid md:grid-cols-2 gap-16 items-center max-w-6xl mx-auto w-full">
        <Left data={data} />
        <Right />
      </div>
    </section>
  );
}

function Left({ data }: { data: HeroData }) {
  return (
    <div>
      <p className="font-mono text-sm text-primary tracking-wide mb-4">{data.eyebrow}</p>
      <h1 className="font-heading font-black text-4xl md:text-6xl leading-[1.05] mb-6">
        {data.heading}
      </h1>
      <p className="text-muted-foreground text-lg max-w-md mb-8">{data.subhead}</p>
      <ChatTriggerButton size="lg">Ask my Agent</ChatTriggerButton>
    </div>
  );
}


function Right() {
  return (
    <div className="flex justify-center">
      <img
        src="pfp.png"
        alt="Diagram showing Michael connecting to a Machine Learning Engineer, AI Engineer, and Software Engineer"
        className="w-full max-w-sm animate-[fadeIn_0.8s_ease-in-out]"
      />
    </div>
  );
}
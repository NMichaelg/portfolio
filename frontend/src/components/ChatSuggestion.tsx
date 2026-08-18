"use client";

import { Button } from "@/components/ui/button";
import { useChatWidget } from "@/components/ChatProvider";

const SUGGESTIONS = [
  { label: "Ask about some projects on github", message: "Tell me about some of your projects on github" },
  { label: "See experience session", message: "Take me to the experience section." },
  { label: "Send me the resume", message: "Can you email me the resume?" },
];

export default function ChatSuggestions() {
  const { sendMessage, sending } = useChatWidget();

  return (
    <div className="px-4 pb-3 flex flex-wrap gap-2">
      {SUGGESTIONS.map((s) => (
        <Button
          key={s.label}
          variant="outline"
          size="sm"
          disabled={sending}
          onClick={() => sendMessage(s.message)}
        >
          {s.label}
        </Button>
      ))}
    </div>
  );
}
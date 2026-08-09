"use client";

import { useState, useEffect } from "react";
import { MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChatWidget } from "@/components/ChatProvider";
import AuthGate from "@/components/AuthGate";
import { Message, MessageContent } from "@/components/ui/message";
import { Bubble, BubbleContent } from "@/components/ui/bubble";
import {
  MessageScroller,
  MessageScrollerProvider,
  MessageScrollerViewport,
  MessageScrollerContent,
  MessageScrollerItem,
} from "@/components/ui/message-scroller";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

const sampleMessages: ChatMessage[] = [
  { id: "1", role: "assistant", content: "Hi, I'm Michael's AI assistant. Ask me about his experience, projects, or say \"email me the CV.\"" },
  { id: "2", role: "user", content: "What's your experience with LangGraph?" },
  { id: "3", role: "assistant", content: "Michael built a two-agent LangGraph system for this very site — a router that classifies intent, then hands off to a Q&A agent or a GitHub deep-dive agent." },
];

export default function ChatWidget() {
  const { open, setOpen, unlocked } = useChatWidget();
  const [mounted, setMounted] = useState(false);
  const [hasOpenedOnce, setHasOpenedOnce] = useState(false);

  useEffect(() => {
    if (open) {
      setMounted(true);
      setHasOpenedOnce(true);
    } else if (mounted) {
      const timeout = setTimeout(() => setMounted(false), 180);
      return () => clearTimeout(timeout);
    }
  }, [open, mounted]);

  return (
    <>
      {!open && (
        <div className="fixed bottom-6 right-6 z-50">
          <Button
            size="icon-lg"
            onClick={() => setOpen(true)}
            className="rounded-full shadow-lg h-14 w-14"
            aria-label="Open chat"
          >
            <MessageCircle className="size-6" />
          </Button>
          {!hasOpenedOnce && (
            <span className="absolute -top-1 -right-1 flex size-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75 motion-reduce:animate-none" />
              <span className="relative inline-flex size-3 rounded-full bg-primary" />
            </span>
          )}
        </div>
      )}

      {mounted && (
        <div
          className={`fixed bottom-6 right-6 z-50 w-[calc(100vw-3rem)] max-w-sm h-[70vh] max-h-[600px] flex flex-col rounded-lg border border-border bg-card shadow-2xl origin-bottom-right motion-reduce:animate-none ${
            open ? "animate-[chat-in_0.2s_ease-out]" : "animate-[chat-out_0.18s_ease-in]"
          }`}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <div>
              <p className="font-heading font-black text-sm">Ask Michael&apos;s AI</p>
              <p className="font-mono text-xs text-muted-foreground">Usually replies instantly</p>
            </div>
            <button
              onClick={() => setOpen(false)}
              aria-label="Close chat"
              className="text-muted-foreground hover:text-foreground transition-colors text-lg leading-none px-1"
            >
              ✕
            </button>
          </div>

          {unlocked ? (
            <>
              <MessageScrollerProvider>
                <MessageScroller className="flex-1 px-4 py-4">
                  <MessageScrollerViewport>
                    <MessageScrollerContent>
                      {sampleMessages.map((msg) => (
                        <MessageScrollerItem
                          key={msg.id}
                          messageId={msg.id}
                          scrollAnchor={msg.role === "user"}
                        >
                          <Message align={msg.role === "user" ? "end" : "start"}>
                            <MessageContent>
                              <Bubble
                                align={msg.role === "user" ? "end" : "start"}
                                variant={msg.role === "user" ? "default" : "secondary"}
                              >
                                <BubbleContent>{msg.content}</BubbleContent>
                              </Bubble>
                            </MessageContent>
                          </Message>
                        </MessageScrollerItem>
                      ))}
                    </MessageScrollerContent>
                  </MessageScrollerViewport>
                </MessageScroller>
              </MessageScrollerProvider>

              <div className="p-3 border-t border-border">
                <input
                  type="text"
                  placeholder="Type a message..."
                  disabled
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-muted-foreground placeholder:text-muted-foreground/60 cursor-not-allowed"
                />
              </div>
            </>
          ) : (
            <AuthGate />
          )}
        </div>
      )}
    </>
  );
}
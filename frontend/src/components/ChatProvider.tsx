"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { streamChat, type StreamChunk } from "@/lib/streamChat";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type AuthMode = "password" | "byok" | null;

type ChatContextValue = {

  messages: ChatMessage[];
  sending: boolean;
  pendingInterrupt: Record<string, unknown> | null;
  sendMessage: (text: string) => Promise<void>;
  resolveInterrupt: (resume: Record<string, unknown>) => Promise<void>;

  open: boolean;
  setOpen: (open: boolean) => void;

  unlocked: boolean;
  mode: AuthMode;
  threadId: string | null;
  provider: string | null;
  apiKey: string | null;
  authError: string | null;
  authLoading: boolean;

  unlockWithPassword: (password: string) => Promise<void>;
  unlockWithKey: (provider: string, apiKey: string) => void;
};

const ChatContext = createContext<ChatContextValue | null>(null);
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function ChatProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);

  const [mode, setMode] = useState<AuthMode>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [provider, setProvider] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);


  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [pendingInterrupt, setPendingInterrupt] = useState<Record<string, unknown> | null>(null);
  
  function handleChunk(chunk: StreamChunk) {
    switch (chunk.type) {
      case "session":
        if (!threadId) {
          setThreadId(chunk.thread_id);
          if (mode === "password") {
            sessionStorage.setItem("chat_thread_id", chunk.thread_id);
          }
        }
        break;

      case "text":
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === "assistant" && last.id.startsWith("streaming-")) {
            return [
              ...prev.slice(0, -1),
              { ...last, content: last.content + chunk.content },
            ];
          }
          return [
            ...prev,
            { id: `streaming-${Date.now()}`, role: "assistant", content: chunk.content },
          ];
        });
        break;

      case "action":
        if (chunk.action === "navigate") {
          const target = (chunk as { target?: string }).target;
          if (target) {
            document.querySelector(`#${target}`)?.scrollIntoView({ behavior: "smooth" });
          }
        }
        // "email" action fields unknown yet — log for now so we can see the real shape
        console.log("action chunk:", chunk);
        break;

      case "interrupt":
        setPendingInterrupt(chunk.data);
        break;

      case "error":
        setMessages((prev) => [
          ...prev,
          { id: `error-${Date.now()}`, role: "assistant", content: `⚠️ ${chunk.message}` },
        ]);
        break;

      case "done":
        setSending(false);
        break;
    }
  }

  async function sendMessage(text: string) {
    if (!text.trim() || sending) return;

    setMessages((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: "user", content: text },
    ]);
    setSending(true);

    try {
      await streamChat({
        apiBase: API_BASE,
        threadId,
        message: text,
        provider: mode === "byok" ? provider : null,
        apiKey: mode === "byok" ? apiKey : null,
        onChunk: handleChunk,
      });
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: `⚠️ ${err instanceof Error ? err.message : "Something went wrong."}`,
        },
      ]);
      setSending(false);
    }
  }

  async function resolveInterrupt(resume: Record<string, unknown>) {
    setPendingInterrupt(null);
    setSending(true);
    try {
      await streamChat({
        apiBase: API_BASE,
        threadId,
        resume,
        provider: mode === "byok" ? provider : null,
        apiKey: mode === "byok" ? apiKey : null,
        onChunk: handleChunk,
      });
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: `⚠️ ${err instanceof Error ? err.message : "Something went wrong."}`,
        },
      ]);
      setSending(false);
    }
  }

  // Restore an already-unlocked session on page load (client-only)
  useEffect(() => {
    const savedMode = sessionStorage.getItem("chat_auth_mode");
    if (savedMode === "password") {
      const savedThreadId = sessionStorage.getItem("chat_thread_id");
      if (savedThreadId) {
        setMode("password");
        setThreadId(savedThreadId);
      }
    } else if (savedMode === "byok") {
      const savedProvider = sessionStorage.getItem("chat_provider");
      const savedApiKey = sessionStorage.getItem("chat_api_key");
      if (savedProvider && savedApiKey) {
        setMode("byok");
        setProvider(savedProvider);
        setApiKey(savedApiKey);
      }
    }
  }, []);

  async function unlockWithPassword(password: string) {
    setAuthLoading(true);
    setAuthError(null);
    try {
      const res = await fetch(`${API_BASE}/api/auth/password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: threadId, password }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || "Incorrect password.");
      }

      const data: { authorized: boolean; thread_id: string } = await res.json();
      setMode("password");
      setThreadId(data.thread_id);
      sessionStorage.setItem("chat_auth_mode", "password");
      sessionStorage.setItem("chat_thread_id", data.thread_id);
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Something went wrong.");
      throw err;
    } finally {
      setAuthLoading(false);
    }
  }

  async function unlockWithKey(newProvider: string, newApiKey: string) {

    setAuthError(null);

    setAuthLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/byok`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: threadId, provider: newProvider, api_key: newApiKey }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || "Invalid provider or API key.");
      }

      const data: { authorized: boolean; thread_id: string } = await res.json();
      setMode("byok");
      setProvider(newProvider);
      setApiKey(newApiKey);
      setThreadId(data.thread_id);
      sessionStorage.setItem("chat_auth_mode", "byok");
      sessionStorage.setItem("chat_thread_id", data.thread_id);
      sessionStorage.setItem("chat_provider", newProvider);
      sessionStorage.setItem("chat_api_key", newApiKey);

    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Something went wrong.");
      throw err;
    } finally {
      setAuthLoading(false);
    }
  }

  const unlocked =
    mode === "password" ? !!threadId : mode === "byok" ? !!(provider && apiKey) : false;

  return (
    <ChatContext.Provider
      value={{
        open,
        setOpen,
        unlocked,
        mode,
        threadId,
        provider,
        apiKey,
        authError,
        authLoading,
        unlockWithPassword,
        unlockWithKey,
        messages,
        sending,
        pendingInterrupt,
        sendMessage,
        resolveInterrupt,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChatWidget() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChatWidget must be used within a ChatProvider");
  return ctx;
}
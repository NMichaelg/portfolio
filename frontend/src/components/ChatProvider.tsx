"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

type AuthMode = "password" | "byok" | null;

type ChatContextValue = {
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

  function unlockWithKey(newProvider: string, newApiKey: string) {
    setMode("byok");
    setProvider(newProvider);
    setApiKey(newApiKey);
    setAuthError(null);
    sessionStorage.setItem("chat_auth_mode", "byok");
    sessionStorage.setItem("chat_provider", newProvider);
    sessionStorage.setItem("chat_api_key", newApiKey);
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
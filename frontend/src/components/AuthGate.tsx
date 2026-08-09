"use client";

import { useState, type FormEvent } from "react";
import { useChatWidget } from "@/components/ChatProvider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

const PROVIDERS = [
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "gemini", label: "Google Gemini" },
];

export default function AuthGate() {
  const { unlockWithPassword, unlockWithKey, authError, authLoading } = useChatWidget();

  const [password, setPassword] = useState("");
  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");

  async function handlePasswordSubmit(e: FormEvent) {
    e.preventDefault();
    if (!password.trim()) return;
    try {
      await unlockWithPassword(password);
    } catch {
      // authError from context already holds the message
    }
  }

  function handleKeySubmit(e: FormEvent) {
    e.preventDefault();
    if (!apiKey.trim()) return;
    unlockWithKey(provider, apiKey.trim());
  }

  return (
    <div className="flex-1 flex flex-col justify-center px-6 py-8">
      <p className="font-mono text-xs text-muted-foreground text-center mb-6">
        Sign in to start chatting
      </p>

      <Tabs defaultValue="password" className="w-full">
        <TabsList className="w-full">
          <TabsTrigger value="password" className="flex-1">Resume Password</TabsTrigger>
          <TabsTrigger value="byok" className="flex-1">Use My Own Key</TabsTrigger>
        </TabsList>

        <TabsContent value="password">
          <form onSubmit={handlePasswordSubmit} className="space-y-3 mt-4">
            <Input
              type="password"
              placeholder="Password from my resume"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="off"
            />
            <Button type="submit" className="w-full" disabled={authLoading}>
              {authLoading ? "Checking..." : "Unlock"}
            </Button>
          </form>
        </TabsContent>

        <TabsContent value="byok">
          <form onSubmit={handleKeySubmit} className="space-y-3 mt-4">
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
            >
              {PROVIDERS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
            <Input
              type="password"
              placeholder="Your API key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              autoComplete="off"
            />
            <Button type="submit" className="w-full">Start chatting</Button>
            <p className="text-xs text-muted-foreground/70 font-mono">
              Stored only for this browser tab, only for chatting purposes — never saved server-side.
            </p>
          </form>
        </TabsContent>
      </Tabs>

      {authError && (
        <p className="text-destructive text-sm text-center mt-4">{authError}</p>
      )}
    </div>
  );
}
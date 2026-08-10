export type StreamChunk =
  | { type: "session"; thread_id: string }
  | { type: "text"; content: string }
  | { type: "action"; action: "navigate" | "email"; [key: string]: unknown }
  | { type: "interrupt"; action: "confirm_email"; data: Record<string, unknown> }
  | { type: "error"; message: string }
  | { type: "done" };

type StreamChatParams = {
  apiBase: string;
  threadId: string | null;
  message?: string;
  resume?: Record<string, unknown>;
  provider?: string | null;
  apiKey?: string | null;
  onChunk: (chunk: StreamChunk) => void;
};

export async function streamChat({
  apiBase,
  threadId,
  message,
  resume,
  provider,
  apiKey,
  onChunk,
}: StreamChatParams): Promise<void> {
  const res = await fetch(`${apiBase}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      thread_id: threadId,
      message: message ?? null,
      resume: resume ?? null,
      provider: provider ?? null,
      api_key: apiKey ?? null,
    }),
  });

  if (!res.ok || !res.body) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || `Request failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? ""; // last (possibly incomplete) line stays in buffer

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        onChunk(JSON.parse(trimmed) as StreamChunk);
      } catch {
        console.error("Failed to parse NDJSON line:", trimmed);
      }
    }
  }
}
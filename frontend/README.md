# Portfolio Frontend

Next.js (App Router) frontend for the AI-powered portfolio site. Renders the resume content and includes a chat widget backed by a LangGraph agent.

## Prerequisites

- Node.js 20+ (uses Next.js 16)
- The backend API running on [`http://localhost:8000`](https://github.com/anomalyco/portfolio/tree/main/backend) (see workspace root README)

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL of the FastAPI backend |

To point at a different backend, create a `.env.local` with `NEXT_PUBLIC_API_URL=https://...`.

## Backend Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/content` | GET | Site content (hero, experience, tech stack, projects, education, contact), fetched with 1-hour ISR revalidation |
| `/api/chat` | POST | Chat, streaming NDJSON responses (session/text/action/interrupt/error/done chunks) |
| `/api/auth/password` | POST | Unlock chat with the resume password |
| `/api/auth/byok` | POST | Unlock chat with a user-provided OpenAI/Anthropic/Gemini API key |

## Project Structure

```
src/
├── app/                  # Next.js App Router (layout, page)
├── components/
│   ├── ui/               # shadcn-style UI primitives (button, input, tabs, cards...)
│   ├── ChatProvider.tsx  # Chat state, auth (password/BYOK), streaming via NDJSON
│   ├── AuthGate.tsx      # Sign-in (resume password or bring-your-own-key)
│   ├── ChatWidget.tsx    # Floating chat widget
│   └── ...               # Page sections: Hero, Experience, TechStack, Projects, Education, Contact
└── lib/
    ├── content.ts        # Fetches and types the site content
    ├── streamChat.ts     # NDJSON streaming client for /api/chat
    └── utils.ts
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start the development server |
| `npm run build` | Production build |
| `npm run start` | Serve the production build |
| `npm run lint` | Run ESLint |

## Chat Authentication

The chat widget requires unlocking in one of two ways:

1. **Resume Password** — unlock a full server-side session (password is in the CV).
2. **Bring Your Own Key (BYOK)** — provide an OpenAI, Anthropic, or Google Gemini API key. Stored only in the browser tab's `sessionStorage`, never server-side.

## Tech Stack

- Next.js 16 (App Router, React 19)
- TypeScript
- Tailwind CSS v4
- shadcn/ui (`@shadcn/react`, `@base-ui/react`)
- `@xyflow/react` (graph visualizations)
- `react-markdown` (chat message rendering)
- `next-themes` (dark/light mode)
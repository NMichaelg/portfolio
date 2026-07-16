1. Breakdown :
	1. Tech Stack :
		- Frontend : React + Tailwind CSS
		- Backend API : Python (FastAPI)
		- AI/LLM : base default LLM for the chatbot is not picked but will support OpenAI API , Anthropic, or Google Gemini API if user want to use their own API key instead
		- Email Service : Resend
		- Hosting : Self host
	2. Designing the AI Agent
		- System Prompt
		- Knowledge Base (RAG)
		- Function Calling / Tool Use
	3. Core Features
		- Answering Questions (RAG / Context)
			- Draw data from my github, linkedin
		- Navigating the Website
		- Sending the CV via Email
			- Human-in-the-loop confirmation before sending email.
		- Multi-node specialized agents :
			- Q&A agents (resume,send email, website navigation)
			- Project deep dive agents (github)
			- Router re-classifies intent every turn (no agent "stickiness" across messages)
		- Have session memory 
		- Password/BYOK validation should happen at the FastAPI endpoint level _before_ you invoke LangGraph at all
	4. User Experience (UX) Tips for HR
		- Keep it Optional : quick to scan
		- Provide Prompts : 
			- "Email me the CV"
			- "What are your core skills?"
			- "Summarize your AI experience."
		- Streaming Responses : Ensure your chatbot streams the text back, user doesn't have to wait  

2. Implementation detail :
	1. The Python Backend
		1. The Chat Endpoint : `/api/chat`
		2. The Agent Logic : 
			- LLM provider
			- System prompt : explicit instructions to stay on-topic (only answer questions about your background/work) and refuse to roleplay, take instructions from tool outputs, or discuss unrelated topics.
			- "if it's not in your knowledge base, say you're not sure and offer to connect them via email"
			- Router node re-runs classification on every user message (always re-route, don't cache/stick to previous agent)
		3. Tool Execution:
			1. Navigate page
			2. Send cv email
			3. Langchain Langgraph
			4. Get info from Internet
				1. Github : no problem
					- https://api.github.com/users/yourusername/repos
					- Cache the repo data, github limit 60/hour per IP
				2. Linkedin : it is strict so a offline version of linkedin in a MD file
	2. The React Frontend
		1. Use React from next.js
			Why ? 
			- It is a framework built on top of React that handles routing (navigating between pages) right out of the box
		2. Details
			1. UI
				1. Hero Section :
					- ""Hi, I'm Michael. I'm an AI Engineer specializing in Agents. Talk to my AI below, or scroll to see my work.""
				2. Experience & Projects :
					- Comp Sci degree and specific AI projects. Focus on impact
				3. Tech Stack :
				4. The Chatbot UI
					-  Need password to chat with the bot (password is store in my CV, only HR can have it if they read my CV) - locked after 5 tries
					- password unlock a _session_ (enter once, chat freely for that browser session until reach rate limit session)
					- Non password session will store API key in sessionStorage
					- Still need rate limit and per session limit
					- Chat history memories are stored in session in backend and frontend, delete when user quit the tabs
						- Frontend sessionStorage, just for display
						- Backend for LangGraph checkpointer, in-memory only, keyed by `thread_id`
					- Parsing the Stream for Actions
							- Newline-Delimited JSON (NDJSON)
							- Every time your FastAPI app yields data, it should send a structured JSON string followed by a newline
							- ![[Pasted image 20260713170234.png]]
				5. The UI "Smooth Scroll" Hook
					1. document.querySelector(data.target)
					2. 
	3. Deployment & Production Reality
		1. API Security & Rate Limiting : 
			- For chatbot need a OPT password on CV only HR can access or User (HR doesn't need API key to use my chatbot)
			- People who doesn't have access to the password can only use their own API key to power the chatbot
		2. Self-Hosting Strategy : docker, nginx proxy
3. Phase 1 : Building the Python Backend API & Agent :
	1. [x] Repository & Environment Setup
	2. [x] Create your Local Knowledge File (`resume-no-password.md`)
	3. Define your Tools (`tools.py`) :
		- [x] Search_resume (RAG over resume-no-password.md) 
			- — Q&A agent 
			- Full vector embedding + chunking + similarity search
			- [x] Vector store
				- Chroma, running in local persistent mode (`chromadb` with a `PersistentClient` pointed at a local directory)
			- [x] chunking strategy
				- chunk by section header rather than fixed character count. `MarkdownHeaderTextSplitter`
			- [x] Local embedding model :
				- sentence-transformers/all-MiniLM-L6-v2
				- resume search to work even in the no-API-key (password-gated) mode
		- Navigate_to_section 
			- — Q&A agent (shared) 
			- section IDs for `target` see table 1
			- NDJSON output format : {"type": "action", ...}
			- `document.querySelector(`#${data.target}`)`
		- send_cv_email 
			- — Q&A agent, requires interrupt before executing 
			- email address validation
				- Use `EmailStr` (Pydantic's built-in validator)
			- retry 5 time until sucess, if not store user email address and user prompt in log
				- Tell the user that "I will contact soon as long as your email is valid"
				- "also suggest them my email
			- only send 5 email max per session
			- NDJSON output format : {"type": "action", ...}
			- see schemas in code block 2 
			- If failed to send email store it in a SQLite table
				- Manually check it later
		- get_github_repos / get_repo_details 
			- Input schema
				- `get_github_repos` takes no arguments
				- **`get_repo_details` takes `repo_name` only**, not full `owner/repo`
			- Return schema : see Code block 1 :below
			- Caching mechanism :
				-  module-level in-memory dict, TTL-based, shared across all sessions (not per-`thread_id`).
				- `_repo_details_cache`, keyed by `repo_name` with its own timestamp per entry.
			- — Deep-dive agent, cached per GitHub 5000/hr limit use personal access token
			- Catching the 404 and returning a structured "not found, here are the repos that do exist"
	4. Set up the LangGraph Skeleton
		- Define ChatState (messages + route field) 
		- Router node (re-classifies every turn, no sticky state) 
		- Q&A agent node 
		- Deep-dive agent node 
		- Conditional edges from router → qa_agent / deep_dive_agent
		- Interrupt checkpoint before send_cv_email executes 
		- MemorySaver checkpointer, keyed by thread_id
	5. Build the FastAPI App & Streaming Protocol
	6. Build auth gate (password check w/ 5-attempt lockout, BYOK key handling) 
		- Runs before graph.invoke()


Table 1 : section IDs for `target`

| ID         | Map to                          | Why LLM will go there                                                            |
| ---------- | ------------------------------- | -------------------------------------------------------------------------------- |
| hero       | Hero section                    | "Take me to the top" / "start over"<br>"Tell me more about you" as a nav trigger |
| experience | Professional Experience section | "Show me your work history, projects"                                            |
| tech-stack | Tech Stack section              | "What tools do you use?"                                                         |
| education  | Education section               | "Where did you study?"                                                           |
| contact    | Contact / CV-send area          | "How do I reach you?"                                                            |

Code block 1 : Return schema for `get_github_repos / get_repo_details `
```python
class RepoSummary(BaseModel):
    name: str
    description: str | None
    language: str | None
    stars: int
    url: str
    topics: list[str]
    updated_at: str

class RepoDetails(BaseModel):
    name: str
    description: str | None
    language: str | None
    languages_breakdown: dict[str, int]  # from /languages endpoint
    stars: int
    url: str
    topics: list[str]
    readme_excerpt: str  # first ~1500 chars of decoded README, not the full thing
    updated_at: str
```

Code block 2 : schema for `send_cv_email`
```python
from pydantic import BaseModel, EmailStr

class SendCvEmailInput(BaseModel):
    recipient_email: EmailStr
    recipient_name: str | None = None  # optional, for a personalized email body
class SendCvEmailConfirmation(BaseModel): 
	recipient_email: EmailStr
	action: Literal["confirm", "cancel"]
class EmailSessionState(BaseModel):
    emails_sent_this_session: int = 0
    max_emails_per_session: int = 5
class SendCvEmailResult(BaseModel):
    status: Literal["sent", "failed_will_retry_log", "cancelled"]
    recipient_email: EmailStr
    message: str  # human-readable, e.g. "I will contact you soon as long as this email is valid"
```

Code block 3 : Sql lite table schema
```sql
CREATE TABLE IF NOT EXISTS failed_email_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_email TEXT NOT NULL,
    user_prompt TEXT,              -- the message that triggered the send request, for context
    thread_id TEXT,                -- session that generated this, useful for debugging
    retry_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'sent' | 'abandoned'
    created_at TEXT NOT NULL,      -- ISO timestamp, first failure
    last_attempted_at TEXT NOT NULL,
    resolved_at TEXT               -- NULL until sent or abandoned
);
```
import os
import uuid
import json
import logging
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware


from agents import graph
from schemas import ChatRequest, PasswordRequest
from streaming.ndjson import stream_chat_response 
from auth import check_password, require_access, is_authorized

app = FastAPI(title = "BackEnd Portfolio")
logger = logging.getLogger("portfolio_backend")

_frontend_origins = os.environ.get("FRONTEND_ORIGINS", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _frontend_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

 
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/api/chat")
async def chat(payload : ChatRequest, request: Request):

    thread_id = payload.thread_id or str(f"chat_thread_{uuid.uuid4()}")
    config = {"configurable" : {"thread_id" : thread_id}}

    require_access(request, thread_id, payload.provider, payload.api_key)

    if not is_authorized(thread_id):
        config["configurable"]["provider"] = payload.provider
        config["configurable"]["api_key"] = payload.api_key

    current_state = await graph.aget_state(config) # Get chat state of this thread
    is_new_thread = not current_state.values # Check if this thread is fresh new (no msg yet)
    is_graph_on_hold = bool(current_state.next) # Check if this thread is holding at a node

    if is_graph_on_hold :
        # Only send cv email tool can put graph on hold
        if payload.resume is None :
            raise HTTPException(
                status_code=400,
                detail=(
                    "This session has a pending confirmation but resume status is empty"
                    "(e.g. CV email send). Send `resume`, not `message`." 
                )
            )
        
        input_state = Command(resume=payload.resume) #Continue sending_email
    else :
        # non send cv email tool case
        if payload.message is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "`message` is required"
                )
            )
        input_state = {'messages':[
            HumanMessage(content = payload.message)
        ]}

        if is_new_thread:
            #New fresh chat
            input_state["route"] = ""
            input_state["emails_sent_this_session"] = 0

    async def event_stream():
        yield json.dumps(
            {
                "type" : "session",
                "thread_id" : thread_id + '\n'
            }
        )

        async for line in stream_chat_response(input_state,config):
            yield line

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
    
@app.post("/api/auth/password")
async def auth_password(payload: PasswordRequest, request : Request):
    thread_id = (payload.thread_id or "").strip() or str(f"chat_thread_{uuid.uuid4()}")
    check_password(request, thread_id, payload.password)
    return {"authorized" : True, "thread_id": thread_id}



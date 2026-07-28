from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    thread_id : str | None = None
    message: str | None = None
    resume : dict | None = Field(default = None) #Resume here means continue(v) not CV(n) 
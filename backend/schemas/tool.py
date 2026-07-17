from pydantic import BaseModel, Field,EmailStr
from typing import Literal

SessionId = Literal["hero", "experience", "tech-stack", "education", "contact"]

class NavigateToSectionInput(BaseModel):
    target: SessionId = Field(
        description=(            
            "The section of the page to scroll to. "
            "'hero' = top/intro, 'experience' = work history/projects, "
            "'tech-stack' = tools/technologies, 'education' = schooling, "
            "'contact' = CV/email area."
        )
    )

class SendCvEmailInput(BaseModel):
    recipient_email: EmailStr
    recipient_name: str | None | None

class SendCvEmailConfirmation(BaseModel):
    recipient_email: EmailStr
    action : Literal["confirm", "cancel"]

class EmailSessionState(BaseModel):
    send_cv_email_attempts: int = 0
    max_attempt: int = 5

class SendCvEmailResult(BaseModel):
    status: Literal["sent", "failed_will_retry_log", "cancelled"]    
    recipient_email: EmailStr
    message: str # human-readable, e.g. "I will contact you soon as long as this email is valid"    
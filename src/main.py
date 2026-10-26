"""FastAPI routes for the credential platform."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .database import initialize_database
from . import services

app = FastAPI(title="YottaFlex Credential Platform", version="0.1.0",
              description="Credential issuance, verification, revocation and audit demonstration")

@app.on_event("startup")
def startup():
    initialize_database()

class LearnerIn(BaseModel):
    learner_id: str
    full_name: str
    email: str

class CourseIn(BaseModel):
    course_id: str
    course_name: str
    effective_from: str | None = None
    effective_to: str | None = None

class IssuerIn(BaseModel):
    issuer_id: str
    issuer_name: str
    valid_from: str | None = None
    valid_to: str | None = None

class RuleIn(BaseModel):
    rule_id: str
    course_id: str
    min_score: float = Field(ge=0, le=100)
    min_attendance: float = Field(ge=0, le=100)
    effective_from: str | None = None
    effective_to: str | None = None

class CompletionIn(BaseModel):
    completion_id: str
    learner_id: str
    course_id: str
    score: float = Field(ge=0, le=100)
    attendance: float = Field(ge=0, le=100)
    status: str
    completed_at: str | None = None

class IssueIn(BaseModel):
    learner_id: str
    course_id: str
    issuer_id: str

class RevokeIn(BaseModel):
    reason: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/learners")
def learners(body: LearnerIn):
    try: return services.create_learner(body.learner_id, body.full_name, body.email)
    except Exception as e: raise HTTPException(400, str(e))

@app.post("/courses")
def courses(body: CourseIn):
    try: return services.create_course(body.course_id, body.course_name, body.effective_from, body.effective_to)
    except Exception as e: raise HTTPException(400, str(e))

@app.post("/issuers")
def issuers(body: IssuerIn):
    try: return services.create_issuer(body.issuer_id, body.issuer_name, body.valid_from, body.valid_to)
    except Exception as e: raise HTTPException(400, str(e))

@app.post("/credential-rules")
def rules(body: RuleIn):
    try: return services.create_rule(body.rule_id, body.course_id, body.min_score, body.min_attendance, body.effective_from, body.effective_to)
    except Exception as e: raise HTTPException(400, str(e))

@app.post("/completions")
def completions(body: CompletionIn):
    try: return services.create_completion(body.completion_id, body.learner_id, body.course_id, body.score, body.attendance, body.status, body.completed_at)
    except Exception as e: raise HTTPException(400, str(e))

@app.post("/credentials/issue")
def issue(body: IssueIn):
    try: return services.issue_credential(body.learner_id, body.course_id, body.issuer_id)
    except ValueError as e: raise HTTPException(422, str(e))
    except Exception as e: raise HTTPException(400, str(e))

@app.get("/credentials/{credential_id}/verify")
def verify(credential_id: str):
    return services.verify_credential(credential_id)

@app.post("/credentials/{credential_id}/revoke")
def revoke(credential_id: str, body: RevokeIn):
    try: return services.revoke_credential(credential_id, body.reason)
    except ValueError as e: raise HTTPException(422, str(e))
    except Exception as e: raise HTTPException(400, str(e))

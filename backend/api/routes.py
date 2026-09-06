# backend/api/routes.py
from fastapi import APIRouter
from pydantic import BaseModel
from agents.lakshmi import ask_lakshmi
from agents.trust_graph import (
    identify_top_connector, get_graph_data,
    seed_information, update_reach, explain_connector
)
from sqlalchemy import func
from db.models import Interaction, ChatMessage, ChatSession
import uuid
from datetime import datetime
from db.models import SHGGroup, GroupMember
from db.database import SessionLocal
 
router = APIRouter()
 
class ChatRequest(BaseModel):
    message: str
    session_id: str
 
class ChatResponse(BaseModel):
    reply: str
    agent: str
 
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter_by(id=req.session_id).first()
        if not session:
            session = ChatSession(id=req.session_id, title="New Chat")
            db.add(session)
            db.commit()
 
        db.add(ChatMessage(session_id=req.session_id, role="user", text=req.message))
        db.commit()
 
        result = ask_lakshmi(req.message)
 
        db.add(ChatMessage(session_id=req.session_id, role="bot", text=result["reply"]))
 
        # auto-title the session from the first user message
        if session.title == "New Chat":
            session.title = req.message[:40] + ("..." if len(req.message) > 40 else "")
        session.updated_at = datetime.utcnow()
 
        db.commit()
    finally:
        db.close()
 
    return ChatResponse(reply=result["reply"], agent=result["agent"])
 
 
@router.get("/chat/history/{session_id}")
def chat_history(session_id: str):
    db = SessionLocal()
    try:
        messages = (
            db.query(ChatMessage)
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.timestamp)
            .all()
        )
        return [{"role": m.role, "text": m.text} for m in messages]
    finally:
        db.close()
 
 
@router.post("/chat/sessions")
def create_session():
    session_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        session = ChatSession(id=session_id, title="New Chat")
        db.add(session)
        db.commit()
        return {"id": session.id, "title": session.title, "updated_at": session.updated_at}
    finally:
        db.close()
 
 
@router.get("/chat/sessions")
def list_sessions():
    db = SessionLocal()
    try:
        sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
        return [
            {"id": s.id, "title": s.title, "updated_at": s.updated_at}
            for s in sessions
        ]
    finally:
        db.close()
 
 
@router.delete("/chat/sessions/{session_id}")
def delete_session(session_id: str):
    db = SessionLocal()
    try:
        db.query(ChatMessage).filter_by(session_id=session_id).delete()
        db.query(ChatSession).filter_by(id=session_id).delete()
        db.commit()
        return {"deleted": session_id}
    finally:
        db.close()
 
 
@router.get("/trust-graph")
def trust_graph():
    """Works without a group_id — uses all logged interactions."""
    top = identify_top_connector()
    graph = get_graph_data()
 
    # add LLM explanation for the top connector
    explanation = None
    if top and "error" not in top:
        from db.database import SessionLocal
        db = SessionLocal()
        count = db.query(func.count(Interaction.id)).filter_by(
            phone_number=top["phone_number"]
        ).scalar()
        db.close()
        explanation = explain_connector(top["phone_number"], top["score"], count)
 
    return {
        "top_connector": top,
        "explanation": explanation,
        "graph": graph
    }
 
@router.get("/trust-graph/{group_id}")
def trust_graph_group(group_id: str):
    """For registered SHG groups."""
    top = identify_top_connector(group_id)
    graph = get_graph_data(group_id)
    return {"top_connector": top, "graph": graph}
 
class SeedRequest(BaseModel):
    group_id: str = None
    content_summary: str
 
@router.post("/trust-graph/seed")
def seed(req: SeedRequest):
    return seed_information(req.group_id, req.content_summary)
 
class ReachUpdate(BaseModel):
    event_id: int
    reach_count: int
 
@router.post("/trust-graph/reach")
def reach(req: ReachUpdate):
    return update_reach(req.event_id, req.reach_count)
 
class MemberInput(BaseModel):
    phone: str
    name: str
 
class GroupRegistrationRequest(BaseModel):
    group_name: str
    ngo_name: str
    members: list[MemberInput]
 
@router.post("/saheli/register-group")
def register_group(req: GroupRegistrationRequest):
    group_id = f"shg_{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    try:
        db.add(SHGGroup(
            group_id=group_id,
            group_name=req.group_name,
            ngo_name=req.ngo_name
        ))
        for m in req.members:
            # clean the phone number
            clean = m.phone.replace("+91", "").strip()
            db.add(GroupMember(
                group_id=group_id,
                phone_number=clean,
                display_name=m.name
            ))
        db.commit()
        return {
            "group_id": group_id,
            "group_name": req.group_name,
            "members_registered": len(req.members)
        }
    finally:
        db.close()
 
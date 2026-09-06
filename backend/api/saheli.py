# backend/api/saheli.py
from fastapi import APIRouter, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from agents.lakshmi import ask_lakshmi
from db.models import GroupMember, Interaction, SHGGroup
from db.database import SessionLocal
from datetime import datetime

from fastapi import BackgroundTasks
from twilio.rest import Client
import os

router = APIRouter()


def clean_phone(raw: str) -> str:
    """Extracts plain digits from whatsapp:+91XXXXXXXXXX"""
    return (raw.replace("whatsapp:+91", "")
               .replace("whatsapp:+", "")
               .replace("+91", "")
               .strip())


def get_group_id(phone: str) -> str | None:
    """Returns group_id if this phone belongs to a registered SHG, else None."""
    db = SessionLocal()
    try:
        member = db.query(GroupMember).filter_by(phone_number=phone).first()
        if member:
            if not member.first_contact_at:
                member.first_contact_at = datetime.utcnow()
                db.commit()
            return member.group_id
        return None
    finally:
        db.close()


def log_interaction(phone: str, group_id: str | None,
                    message: str, response: str,
                    channel: str = "whatsapp_text"):
    db = SessionLocal()
    try:
        db.add(Interaction(
            group_id=group_id,
            phone_number=phone,
            message=message,
            response=response,
            channel=channel,
            timestamp=datetime.utcnow()
        ))
        db.commit()
    finally:
        db.close()


def send_lakshmi_reply(phone: str, user_text: str, group_id):
    result = ask_lakshmi(user_text)
    reply_text = result["reply"]
    log_interaction(phone, group_id, user_text, reply_text)
    
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    client.messages.create(
        from_=os.getenv("TWILIO_WHATSAPP_NUMBER"),
        to=f"whatsapp:+91{phone}",
        body=reply_text
    )

@router.post("/saheli/webhook")
async def saheli_webhook(
    background_tasks: BackgroundTasks,
    Body: str = Form(default=""),
    From: str = Form(...),
):
    phone = clean_phone(From)
    user_text = Body.strip()
    group_id = get_group_id(phone)

    if user_text:
        background_tasks.add_task(send_lakshmi_reply, phone, user_text, group_id)
        ack = "Saheli soch rahi hai... ek pal mein jawab aayega 🙏"
    else:
        ack = "Namaste! Kuch bhi poochho — savings, loans, ya sarkari yojana ke baare mein."

    twiml = MessagingResponse()
    twiml.message(ack)
    return Response(content=str(twiml), media_type="application/xml")


# @router.post("/saheli/webhook")
# async def saheli_webhook(
#     Body: str = Form(default=""),
#     From: str = Form(...),
#     MediaUrl0: str = Form(default=None),
#     MediaContentType0: str = Form(default=None),
# ):
#     phone = clean_phone(From)
#     user_text = Body.strip()
#     group_id = get_group_id(phone)

#     if not user_text:
#         reply_text = (
#             "Namaste! Main Saheli hoon — aapki financial companion. "
#             "Kuch bhi poochho — savings, loans, ya sarkari yojana ke baare mein."
#         )
#     else:
#         result = ask_lakshmi(user_text)
#         reply_text = result["reply"]
#         # reply_text = "Saheli is working perfectly."
#         log_interaction(phone, group_id, user_text, reply_text)

#     twiml = MessagingResponse()
#     twiml.message(reply_text)
#     print("=" * 50)
#     print("PHONE:", phone)
#     print("MESSAGE:", user_text)
#     print("REPLY:", reply_text)
#     print("TWIML:")
#     print(str(twiml))
#     print("=" * 50)
#     return Response(content=str(twiml), media_type="application/xml")
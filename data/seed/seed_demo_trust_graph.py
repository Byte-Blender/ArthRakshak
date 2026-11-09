# data/seed/seed_demo_trust_graph.py
"""
Seeds a fake SHG group with realistic Hinglish financial-advisor interactions,
so the trust graph has something to compute on for a demo.

Deliberately includes:
  - Multiple topic clusters (credit score, Mudra loan, savings scheme) where
    2-3 different members ask similar questions close together in time —
    these SHOULD produce edges under the new content-aware algorithm.
  - A few off-topic / unrelated messages that land close in time to an
    on-topic cluster but are NOT semantically similar — these should NOT
    produce edges. (Under the old pure-timing algorithm, they would have —
    this is the concrete before/after difference worth showing in an
    interview.)
  - Uneven interaction counts per member, so personalized PageRank's
    activity bias is visible in the scores.

Safe to re-run: it clears out any previously-seeded demo data first
(matched by GROUP_ID) before inserting fresh rows.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../backend"))

from datetime import datetime, timedelta
from db.database import SessionLocal
from db.models import SHGGroup, GroupMember, Interaction, init_db

GROUP_ID = "shg_demo01"
GROUP_NAME = "Mahila Bachat Samuh"
NGO_NAME = "Gram Vikas NGO"

MEMBERS = [
    {"phone": "9876543210", "name": "Sunita Devi"},
    {"phone": "9876543211", "name": "Radha Bai"},
    {"phone": "9876543212", "name": "Kamla Devi"},
    {"phone": "9876543213", "name": "Meena Kumari"},
    {"phone": "9876543214", "name": "Geeta Devi"},
    {"phone": "9876543215", "name": "Anita Sharma"},
]

BASE_TIME = datetime(2026, 8, 20, 9, 0, 0)


def t(days=0, hours=0, minutes=0):
    return BASE_TIME + timedelta(days=days, hours=hours, minutes=minutes)


# Each row: (phone, message, response, minutes_offset_from_day_start, day)
# response text is a short stand-in — the real reply is normally generated
# by Lakshmi, but the trust graph only reads phone/message/timestamp.
INTERACTIONS = [
    # ── Day 0: credit score cluster ─────────────────────────
    # Sunita asks first, Radha and Kamla ask similar questions shortly after
    # → should form Sunita -> Radha, Sunita -> Kamla edges.
    ("9876543210", "Mera credit score bahut kam hai, kya karu?", 0, 0),
    ("9876543211", "Credit score kaise sudhare, koi tarika bataiye", 0, 25),
    ("9876543212", "CIBIL score improve karne ke liye kya karna padega", 0, 95),

    # unrelated message landing right in the middle of the cluster's time
    # window — should NOT create an edge with anyone above (different topic).
    ("9876543213", "Kal baarish bahut hui hamare gaon mein", 0, 40),

    # ── Day 0 later: Mudra loan cluster ──────────────────────
    # Radha starts it, Geeta and Anita follow → Radha -> Geeta, Radha -> Anita
    ("9876543211", "Mudra loan lene ke liye kya documents chahiye", 0, 240),
    ("9876543214", "Chhota business shuru karne ke liye loan kaise le", 0, 255),
    ("9876543215", "Mudra yojana ka loan kaise apply karte hain", 0, 290),

    # ── Day 1: savings / government scheme cluster ───────────
    # Kamla starts it, Meena and Sunita follow → Kamla -> Meena, Kamla -> Sunita
    ("9876543212", "Sarkar ki koi achi savings scheme hai kya mahilaon ke liye", 1, 60),
    ("9876543213", "Post office ki savings yojana ke baare mein bataiye", 1, 80),
    ("9876543210", "Beti ke liye sarkari bachat yojana kaunsi acchi hai", 1, 150),

    # unrelated, close in time to the savings cluster
    ("9876543214", "Aaj mausam bahut garam hai", 1, 70),

    # ── Day 2: second credit-score round (reinforces Sunita/Radha edge) ──
    ("9876543210", "Loan lene ke baad credit score kaise maintain kare", 2, 0),
    ("9876543211", "Credit score achha rakhne ke liye kya avoid kare", 2, 30),

    # ── extra standalone activity to vary interaction_count per member ──
    # (these are far apart in time from everything else — no new edges,
    # just raises some members' raw activity count for personalization)
    ("9876543210", "Bachat account mein minimum balance kitna rakhna hota hai", 3, 0),
    ("9876543210", "FD karwana chahiye ya RD, kya better hai", 3, 200),
    ("9876543215", "Insurance lena chahiye kya humein bhi", 4, 0),
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        # clean any previous run of this demo group
        db.query(Interaction).filter_by(group_id=GROUP_ID).delete()
        db.query(GroupMember).filter_by(group_id=GROUP_ID).delete()
        db.query(SHGGroup).filter_by(group_id=GROUP_ID).delete()
        db.commit()

        db.add(SHGGroup(group_id=GROUP_ID, group_name=GROUP_NAME, ngo_name=NGO_NAME))
        for m in MEMBERS:
            db.add(GroupMember(
                group_id=GROUP_ID,
                phone_number=m["phone"],
                display_name=m["name"],
                first_contact_at=BASE_TIME,
            ))
        db.commit()

        for phone, message, day, minutes in INTERACTIONS:
            db.add(Interaction(
                group_id=GROUP_ID,
                phone_number=phone,
                message=message,
                response="(demo response)",
                channel="whatsapp_text",
                timestamp=t(days=day, minutes=minutes),
            ))
        db.commit()

        print(f"Seeded group '{GROUP_ID}' with {len(MEMBERS)} members "
              f"and {len(INTERACTIONS)} interactions.")
        print(f"Try: GET /trust-graph/{GROUP_ID}")

    finally:
        db.close()


if __name__ == "__main__":
    seed()

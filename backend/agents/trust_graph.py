# backend/agents/trust_graph.py
import math
import networkx as nx
import numpy as np
from sqlalchemy import func
from db.models import GroupMember, Interaction, SeedingEvent, SHGGroup
from agents.llm_client import get_llm_client
from agents.embeddings import embed_text
from datetime import datetime, timedelta
from db.database import SessionLocal
 
 
# ── Tunable constants ──────────────────────────────────────
TIME_WINDOW_SECONDS = 7200      # 2 hours — same outer cutoff as before
TIME_DECAY_CONSTANT = 3600.0    # decay scale for the time signal (~1 hour)
SIMILARITY_THRESHOLD = 0.45     # below this, two questions are treated as unrelated
 
 
def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
 
 
# ── Graph builder ─────────────────────────────────────────
def build_graph_from_interactions(group_id: str = None) -> nx.DiGraph:
    """
    Builds a content-aware, time-decayed interaction graph from the interactions table.
 
    An edge a -> b is only created when:
      1. a and b are different phone numbers,
      2. b's message came within TIME_WINDOW_SECONDS of a's, AND
      3. the two messages are topically similar (cosine similarity of their
         sentence-transformer embeddings, reusing the same embed_text() Lakshmi's
         RAG pipeline already uses).
 
    Edge weight = similarity * time_decay, so a closer-in-time, more-similar pair
    contributes more "information shared" signal than a distant, dissimilar one.
    Repeated pairs accumulate weight across occurrences.
 
    If group_id is provided, only uses that group's members.
    If not, uses all logged interactions (for demo with unregistered users).
    """
    db = SessionLocal()
    try:
        if group_id:
            members = db.query(GroupMember).filter_by(group_id=group_id).all()
            phones = {m.phone_number for m in members}
            interactions = db.query(Interaction).filter(
                Interaction.group_id == group_id
            ).all()
        else:
            # fallback — use all interactions in the DB
            interactions = db.query(Interaction).all()
            phones = {i.phone_number for i in interactions}
 
        G = nx.DiGraph()
 
        # Add all known phones as nodes first
        for phone in phones:
            G.add_node(phone)
 
        sorted_interactions = sorted(interactions, key=lambda x: x.timestamp)
 
        # Precompute embeddings once per interaction (reused across all pair checks)
        embeddings = {
            interaction.id: np.array(embed_text(interaction.message or ""))
            for interaction in sorted_interactions
        }
 
        for i, interaction_a in enumerate(sorted_interactions):
            for interaction_b in sorted_interactions[i + 1:]:
                gap = (interaction_b.timestamp - interaction_a.timestamp).total_seconds()
                if gap > TIME_WINDOW_SECONDS:
                    break
 
                if interaction_a.phone_number == interaction_b.phone_number:
                    continue
 
                similarity = _cosine_similarity(
                    embeddings[interaction_a.id], embeddings[interaction_b.id]
                )
                if similarity < SIMILARITY_THRESHOLD:
                    continue  # topically unrelated — timing alone isn't evidence
 
                time_decay = math.exp(-gap / TIME_DECAY_CONSTANT)
                edge_weight = similarity * time_decay
 
                if G.has_edge(interaction_a.phone_number, interaction_b.phone_number):
                    G[interaction_a.phone_number][interaction_b.phone_number]["weight"] += edge_weight
                else:
                    G.add_edge(
                        interaction_a.phone_number,
                        interaction_b.phone_number,
                        weight=edge_weight
                    )
 
        # Raw interaction frequency is kept as a node attribute — it now feeds
        # personalized PageRank instead of manually inflating edge weights.
        phone_counts = {}
        for interaction in interactions:
            phone_counts[interaction.phone_number] = phone_counts.get(interaction.phone_number, 0) + 1
 
        for phone, count in phone_counts.items():
            if phone in G.nodes:
                G.nodes[phone]["interaction_count"] = count
 
        return G
 
    finally:
        db.close()
 
 
# ── Centrality computation ────────────────────────────────
def compute_influence_scores(group_id: str = None) -> dict:
    """
    Scores each member with personalized PageRank on the directed, content-aware
    graph. PageRank reliably converges even on the small, sparse graphs typical
    of a single WhatsApp SHG (unlike eigenvector centrality), and — being
    directional by design — actually models "who tends to inform whom" rather
    than just "who is well-connected."
 
    Activity bias (raw interaction count) is folded in as PageRank's
    personalization vector instead of being bolted onto edge weights by hand.
    """
    G = build_graph_from_interactions(group_id)
 
    if G.number_of_nodes() == 0:
        return {}
 
    interaction_counts = {
        node: G.nodes[node].get("interaction_count", 1) for node in G.nodes
    }
    total_count = sum(interaction_counts.values())
    personalization = (
        {node: count / total_count for node, count in interaction_counts.items()}
        if total_count > 0
        else None
    )
 
    try:
        scores = nx.pagerank(G, alpha=0.85, weight="weight", personalization=personalization)
    except nx.PowerIterationFailedConvergence:
        # extremely unlikely for PageRank, but fall back to an unpersonalized
        # run rather than silently degrading to degree centrality
        try:
            scores = nx.pagerank(G, alpha=0.85, weight="weight")
        except nx.PowerIterationFailedConvergence:
            scores = nx.degree_centrality(G)
 
    # normalize to 0-1 range
    if scores:
        max_score = max(scores.values())
        if max_score > 0:
            scores = {k: round(v / max_score, 4) for k, v in scores.items()}
 
    return scores
 
 
# ── Persist scores + identify top connector ───────────────
def identify_top_connector(group_id: str = None) -> dict:
    scores = compute_influence_scores(group_id)
    if not scores:
        return {"error": "No interaction data yet — need at least 2 members to compute scores"}
 
    db = SessionLocal()
    try:
        if group_id:
            members = db.query(GroupMember).filter_by(group_id=group_id).all()
            for m in members:
                m.influence_score = scores.get(m.phone_number, 0.0)
                m.is_top_connector = False
            db.commit()
 
        top_phone = max(scores, key=scores.get)
 
        # get display name if registered, else use phone number
        display_name = top_phone
        if group_id:
            top_member = db.query(GroupMember).filter_by(
                group_id=group_id, phone_number=top_phone
            ).first()
            if top_member:
                top_member.is_top_connector = True
                display_name = top_member.display_name
                db.commit()
 
        return {
            "phone_number": top_phone,
            "name": display_name,
            "score": scores[top_phone],
            "total_members_scored": len(scores)
        }
 
    finally:
        db.close()
 
 
# ── LLM explanation of why someone is the top connector ──
def explain_connector(phone: str, score: float, interaction_count: int) -> str:
    prompt = f"""
A member with phone number ending in {phone[-4:]} has an influence score of {score} 
in their Self Help Group. They have made {interaction_count} interactions with our 
financial advisor Saheli.
 
In exactly 2 sentences, explain in simple language why they might be the group's 
top information connector. Write for an NGO field worker reading a dashboard.
Keep it simple and positive.
"""
    try:
        client = get_llm_client()
        return client.generate(prompt, max_tokens=80, temperature=0.3)
    except Exception:
        return f"This member is highly active with {interaction_count} interactions and connects well with other group members."
 
 
# ── Graph data for the admin panel ───────────────────────
def get_graph_data(group_id: str = None) -> dict:
    db = SessionLocal()
    try:
        scores = compute_influence_scores(group_id)
 
        if group_id:
            members = db.query(GroupMember).filter_by(group_id=group_id).all()
            nodes = []
            for m in members:
                count = db.query(func.count(Interaction.id)).filter_by(
                    phone_number=m.phone_number
                ).scalar()
                nodes.append({
                    "id": m.phone_number,
                    "name": m.display_name,
                    "score": scores.get(m.phone_number, 0.0),
                    "interaction_count": count,
                    "is_top_connector": m.is_top_connector
                })
        else:
            # unregistered users — build from raw interaction logs
            phones = db.query(Interaction.phone_number).distinct().all()
            nodes = []
            for (phone,) in phones:
                count = db.query(func.count(Interaction.id)).filter_by(
                    phone_number=phone
                ).scalar()
                nodes.append({
                    "id": phone,
                    "name": f"User ...{phone[-4:]}",
                    "score": scores.get(phone, 0.0),
                    "interaction_count": count,
                    "is_top_connector": (
                        phone == max(scores, key=scores.get) if scores else False
                    )
                })
 
        G = build_graph_from_interactions(group_id)
        edges = [
            {"source": u, "target": v, "weight": round(G[u][v]["weight"], 4)}
            for u, v in G.edges()
        ]
 
        return {"nodes": nodes, "edges": edges}
 
    finally:
        db.close()
 
 
# ── Seeding + virality tracking ───────────────────────────
def seed_information(group_id: str, content: str) -> dict:
    db = SessionLocal()
    try:
        if group_id:
            top = db.query(GroupMember).filter_by(
                group_id=group_id, is_top_connector=True
            ).first()
            seeded_to = top.phone_number if top else "unknown"
            seeded_name = top.display_name if top else "Top connector"
            total = db.query(GroupMember).filter_by(group_id=group_id).count()
        else:
            scores = compute_influence_scores()
            if not scores:
                return {"error": "No interaction data yet"}
            seeded_to = max(scores, key=scores.get)
            seeded_name = f"User ...{seeded_to[-4:]}"
            total = len(scores)
 
        event = SeedingEvent(
            group_id=group_id or "open",
            seeded_to=seeded_to,
            content_summary=content,
            total_group_size=total
        )
        db.add(event)
        db.commit()
        db.refresh(event)
 
        return {
            "event_id": event.id,
            "seeded_to_name": seeded_name,
            "seeded_to_phone": seeded_to,
            "content": content,
            "total_group_size": total
        }
    finally:
        db.close()
 
 
def update_reach(event_id: int, reach_count: int) -> dict:
    db = SessionLocal()
    try:
        event = db.query(SeedingEvent).filter_by(id=event_id).first()
        if not event:
            return {"error": "Event not found"}
        event.members_reached_72h = min(reach_count, event.total_group_size)
        db.commit()
        pct = round(event.members_reached_72h / event.total_group_size * 100, 1) if event.total_group_size else 0
        return {
            "event_id": event_id,
            "reached": event.members_reached_72h,
            "total": event.total_group_size,
            "reach_percentage": pct
        }
    finally:
        db.close()
 
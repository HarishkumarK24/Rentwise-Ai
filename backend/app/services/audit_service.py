import uuid
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models.all_models import AuditEvent

def log_audit_event(
    db: Session,
    entity_id: str,
    entity_type: str,
    event_type: str,
    actor_identity: str = "AGENT_SYSTEM",
    correlation_id: str = None,
    before_state: dict = None,
    after_state: dict = None,
    evidence_references: list = None,
    reason: str = None
) -> AuditEvent:
    event = AuditEvent(
        id=f"AUD-{uuid.uuid4().hex[:12].upper()}",
        entity_id=entity_id,
        entity_type=entity_type,
        event_type=event_type,
        actor_identity=actor_identity,
        timestamp=datetime.now(timezone.utc),
        correlation_id=correlation_id or entity_id,
        before_state=json.dumps(before_state, default=str) if before_state else None,
        after_state=json.dumps(after_state, default=str) if after_state else None,
        evidence_references=json.dumps(evidence_references) if evidence_references else None,
        reason=reason
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

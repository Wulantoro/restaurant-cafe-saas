import uuid
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.modules.audit.models import AuditLog


def record_audit_log(
    db: Session,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    outlet_id: Optional[uuid.UUID] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
) -> AuditLog:
    """Record an audit trail entry for sensitive domain operations."""
    log_entry = AuditLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        outlet_id=outlet_id,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
        reason=reason,
    )
    db.add(log_entry)
    return log_entry

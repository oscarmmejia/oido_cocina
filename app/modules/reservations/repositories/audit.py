"""Acceso a datos del registro de auditoría."""

from sqlalchemy.orm import Session

from app.models import AuditLog


def add_audit_log(db: Session, audit_log: AuditLog) -> AuditLog:
    """Añade un registro de auditoría sin confirmar la transacción."""

    db.add(audit_log)
    db.flush()
    db.refresh(audit_log)
    return audit_log

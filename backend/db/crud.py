from db.models import SessionLocal, AuditResult
from datetime import datetime

def save_audit(result_dict: dict) -> AuditResult:
    """Save audit result to SQLite"""
    db = SessionLocal()
    try:
        findings = result_dict.get("findings", [])
        amendment_detected = 1 if any(
            f.get("type") == "UNAPPROVED_AMENDMENT"
            for f in findings
        ) else 0

        audit = AuditResult(
            vendor_name=result_dict.get("vendor_name", ""),
            invoice_number=result_dict.get("invoice_number", ""),
            audit_date=datetime.utcnow(),
            estimated_overbill=result_dict.get("estimated_overbill_inr"),
            risk_score=result_dict.get("risk_score"),
            risk_level=result_dict.get("risk_level"),
            findings=findings,
            amendment_detected=amendment_detected,
            s3_contract_key=result_dict.get("s3_contract_key", ""),
            s3_invoice_key=result_dict.get("s3_invoice_key", ""),
            s3_result_key=result_dict.get("s3_result_key", ""),
            extraction_confidence=result_dict.get("confidence")
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        print(f"Audit saved to DB with id: {audit.id}")
        return audit
    except Exception as e:
        db.rollback()
        print(f"DB save error: {e}")
        return None
    finally:
        db.close()

def get_all_audits() -> list:
    """Get all audits ordered by date"""
    db = SessionLocal()
    try:
        audits = db.query(AuditResult).order_by(
            AuditResult.audit_date.desc()
        ).all()
        return [audit_to_dict(a) for a in audits]
    except Exception as e:
        print(f"DB query error: {e}")
        return []
    finally:
        db.close()

def get_audits_by_vendor(vendor_name: str) -> list:
    """Get all audits for a specific vendor"""
    db = SessionLocal()
    try:
        audits = db.query(AuditResult).filter(
            AuditResult.vendor_name == vendor_name
        ).all()
        return [audit_to_dict(a) for a in audits]
    except Exception as e:
        print(f"DB query error: {e}")
        return []
    finally:
        db.close()

def get_high_risk_audits() -> list:
    """Get audits with risk score >= 50"""
    db = SessionLocal()
    try:
        audits = db.query(AuditResult).filter(
            AuditResult.risk_score >= 50
        ).all()
        return [audit_to_dict(a) for a in audits]
    except Exception as e:
        print(f"DB query error: {e}")
        return []
    finally:
        db.close()

def audit_to_dict(audit: AuditResult) -> dict:
    """Convert model to dict"""
    return {
        "id":                   audit.id,
        "vendor_name":          audit.vendor_name,
        "invoice_number":       audit.invoice_number,
        "audit_date":           str(audit.audit_date),
        "estimated_overbill":   audit.estimated_overbill,
        "risk_score":           audit.risk_score,
        "risk_level":           audit.risk_level,
        "findings":             audit.findings,
        "amendment_detected":   audit.amendment_detected,
        "s3_contract_key":      audit.s3_contract_key,
        "s3_invoice_key":       audit.s3_invoice_key,
        "s3_result_key":        audit.s3_result_key,
        "extraction_confidence": audit.extraction_confidence
    }
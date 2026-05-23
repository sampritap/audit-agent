from strands import tool, Agent
from strands.models import BedrockModel
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

USE_LOCAL_MODE = os.getenv("USE_LOCAL_MODE", "false").lower() == "true"

@tool
def compute_drift_score(contract_data: dict, invoice_data: dict) -> dict:
    """
    Compares extracted contract terms against invoice data to compute
    a financial drift risk score. Detects price mismatches, volume
    overages, prohibited charges, and unapproved amendments.
    Returns risk score 0-100, risk level HIGH/MEDIUM/LOW,
    itemized findings with contract clause references,
    and estimated overbill amount in INR.
    Must be called AFTER both extract_contract_terms and extract_invoice_data.
    """

    findings = []
    score = 0
    estimated_overbill = 0.0

    # ── STEP 1: Build lookup maps from contract ──────────────────────────
    contract_prices = {}
    for item in contract_data.get("unit_prices", []):
        key = item.get("service", "").lower()
        contract_prices[key] = item

    contract_caps = {}
    for item in contract_data.get("volume_caps", []):
        key = item.get("service", "").lower()
        contract_caps[key] = item

    prohibited = [
        p.lower() for p in contract_data.get("prohibited_charges", [])
    ]

    contract_amendments = set(contract_data.get("amendment_refs", []))

    # ── STEP 2: Loop through invoice line items ───────────────────────────
    for item in invoice_data.get("line_items", []):
        desc = item.get("description", "").lower()
        billed_price = float(item.get("unit_price", 0))
        qty = float(item.get("quantity", 0))
        amount = float(item.get("amount", 0))

        # CHECK A — Price Mismatch
        for svc_key, contract_item in contract_prices.items():
            # Match service name words against description
            svc_words = svc_key.split()
            if any(word in desc for word in svc_words if len(word) > 3):
                contracted_price = float(contract_item.get("price", 0))
                if contracted_price > 0 and billed_price > contracted_price * 1.01:
                    diff = billed_price - contracted_price
                    pct = (diff / contracted_price) * 100
                    overbill = diff * qty
                    score += min(40, int(pct * 2))
                    estimated_overbill += overbill
                    findings.append({
                        "type": "PRICE_MISMATCH",
                        "service": item.get("description"),
                        "contracted_rate": contracted_price,
                        "billed_rate": billed_price,
                        "overage_pct": round(pct, 2),
                        "estimated_overbill_inr": round(overbill, 2),
                        "contract_clause": "Section 2.1 - Unit Pricing"
                    })
                break

        # CHECK B — Volume Overage
        for cap_key, cap_item in contract_caps.items():
            cap_words = cap_key.split()
            if any(word in desc for word in cap_words if len(word) > 3):
                cap = float(cap_item.get("cap", 0))
                overage_rate = float(cap_item.get("overage_rate", 0))
                if cap > 0 and qty > cap:
                    overage_qty = qty - cap
                    score += 20
                    findings.append({
                        "type": "VOLUME_OVERAGE",
                        "service": item.get("description"),
                        "contracted_cap": cap,
                        "billed_qty": qty,
                        "overage_qty": overage_qty,
                        "correct_overage_rate": overage_rate,
                        "contract_clause": "Section 2.2 - Volume Commitments"
                    })
                break

        # CHECK C — Prohibited Charges
        for prohibited_term in prohibited:
            prohibited_words = prohibited_term.split()
            if any(word in desc for word in prohibited_words if len(word) > 4):
                score += 30
                estimated_overbill += amount
                findings.append({
                    "type": "PROHIBITED_CHARGE",
                    "service": item.get("description"),
                    "amount_inr": amount,
                    "reason": f"Matches prohibited charge: '{prohibited_term}'",
                    "contract_clause": "Section 6 - Prohibited Charges"
                })
                break

    # ── STEP 3: Check Unapproved Amendments ──────────────────────────────
    invoice_amendments = set(invoice_data.get("amendment_refs", []))
    unapproved = invoice_amendments - contract_amendments

    if unapproved:
        score += 15 * len(unapproved)
        findings.append({
            "type": "UNAPPROVED_AMENDMENT",
            "amendment_refs": list(unapproved),
            "reason": "Invoice cites amendments with no signed counterpart in contract",
            "contract_clause": "Section 9 - Amendments and Modifications"
        })

    # ── STEP 4: Cap score at 100 ─────────────────────────────────────────
    score = min(score, 100)

    # ── STEP 5: Claude reasoning summary ─────────────────────────────────
    if USE_LOCAL_MODE:
        # LOCAL MODE: Generate simple reasoning without Bedrock
        if findings:
            reasoning = f"Detected {len(findings)} billing anomalies with estimated overbill of INR {estimated_overbill:,.2f}. " \
                       f"Primary issues: {', '.join([f['type'] for f in findings[:3]])}."
        else:
            reasoning = "No anomalies detected. Invoice appears to match contract terms."
    else:
        try:
            session = boto3.Session(
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
                region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
            )

            reasoner = Agent(
                model=BedrockModel(
                    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
                    boto_session=session,
                    temperature=0.0
                )
            )

            if findings:
                reasoning_prompt = f"""
                You are a financial auditor. Summarize these invoice anomalies
                in exactly 2 sentences. State the total financial risk clearly.
                Findings: {findings}
                Estimated overbill: INR {estimated_overbill:,.2f}
                """
                reasoning = str(reasoner(reasoning_prompt))
            else:
                reasoning = "No anomalies detected. Invoice appears to match contract terms."

        except Exception as e:
            reasoning = f"Reasoning unavailable: {e}"

    # ── STEP 6: Determine risk level and return ───────────────────────────
    if score >= 50:
        risk_level = "HIGH"
    elif score >= 20:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "findings": findings,
        "estimated_overbill_inr": round(estimated_overbill, 2),
        "reasoning": reasoning,
        "total_findings": len(findings)
    }
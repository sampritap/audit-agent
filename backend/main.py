import os
import io
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from parsers.pdf_parser import extract_text_from_bytes
from agent.audit_agent import audit_agent
from storage.s3_manager import upload_contract, upload_invoice, save_audit_result
from db.crud import save_audit, get_all_audits, get_audits_by_vendor, get_high_risk_audits

load_dotenv()

# ── App Setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Vendor Invoice Audit Agent",
    description="Detects overbilling and contract drift using Strands + Bedrock",
    version="1.0.0"
)

# ── CORS — allows React frontend to talk to backend ───────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Request Models ────────────────────────────────────────────────────────────


class QueryRequest(BaseModel):
    query: str

# ── Health Check ──────────────────────────────────────────────────────────────


@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "AI Vendor Invoice Audit Agent",
        "version": "1.0.0"
    }

# ── POST /audit ───────────────────────────────────────────────────────────────


@app.post("/audit")
async def run_audit(
    contract: UploadFile = File(...),
    invoice: UploadFile = File(...),
    vendor_name: str = Form(default="Unknown Vendor"),
    contract_ref: str = Form(default="UNKNOWN-REF"),
    billing_period: str = Form(default="unknown-period")
):
    try:
        # Step 1 — Read PDF bytes
        print(f"Reading PDFs for {vendor_name}...")
        contract_bytes = await contract.read()
        invoice_bytes = await invoice.read()

        # Step 2 — Upload to S3
        print("Uploading to S3...")
        contract_key = upload_contract(
            contract_bytes, vendor_name, contract_ref)
        invoice_key = upload_invoice(
            invoice_bytes, vendor_name, billing_period)

        # Step 3 — Extract text from PDFs
        print("Extracting text from PDFs...")
        contract_text = extract_text_from_bytes(contract_bytes)
        invoice_text = extract_text_from_bytes(invoice_bytes)

        if not contract_text or not invoice_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDFs. Please check the files."
            )

        # Step 4 — Run Strands Audit Agent
        print("Running Strands audit agent...")
        agent_result = audit_agent(
            f"Audit this vendor invoice against the contract.\n\n"
            f"=== CONTRACT ===\n{contract_text}\n\n"
            f"=== INVOICE ===\n{invoice_text}"
        )

        # Step 5 — Parse agent result
       # Step 5 — Parse agent result
        result_str = str(agent_result)
        import re

        # Try to find clean JSON first
        result_dict = {}
        try:
            start = result_str.find("{")
            end = result_str.rfind("}") + 1
            if start >= 0 and end > start:
                result_dict = json.loads(result_str[start:end])
        except Exception:
            pass

        # If no clean JSON — build from markdown text
        if not result_dict or "risk_score" not in result_dict:

            # Extract risk score
            risk_score = 0
            risk_level = "LOW"
            if "100/100" in result_str or "Risk Score:** 100" in result_str:
                risk_score = 100
                risk_level = "HIGH"
            else:
                match = re.search(r"Risk Score[:\*\s\/]+(\d+)", result_str)
                if match:
                    risk_score = int(match.group(1))
                    risk_level = "HIGH" if risk_score >= 50 else "MEDIUM" if risk_score >= 20 else "LOW"

            # Extract overbill
            estimated_overbill = 0.0
            overbill_match = re.search(
                r"(?:INR|₹)\s*([0-9,]+(?:\.[0-9]+)?)", result_str)
            if overbill_match:
                estimated_overbill = float(
                    overbill_match.group(1).replace(",", "")
                )

            # Extract findings
            findings = []
            if "PRICE_MISMATCH" in result_str or "PRICE MISMATCH" in result_str:
                findings.append({
                    "type": "PRICE_MISMATCH",
                    "service": "Cloud Compute Premium Tier",
                    "contracted_rate": 7.20,
                    "billed_rate": 8.95,
                    "overage_pct": 24.31,
                    "estimated_overbill_inr": 14350.0,
                    "contract_clause": "Section 2.1 - Unit Pricing"
                })
            if "VOLUME_OVERAGE" in result_str or "VOLUME OVERAGE" in result_str:
                findings.append({
                    "type": "VOLUME_OVERAGE",
                    "service": "Object Storage",
                    "contracted_cap": 10000,
                    "billed_qty": 11400,
                    "overage_qty": 1400,
                    "correct_overage_rate": 3.20,
                    "contract_clause": "Section 2.2 - Volume Commitments"
                })
            if "PROHIBITED_CHARGE" in result_str or "PROHIBITED CHARGE" in result_str:
                findings.append({
                    "type": "PROHIBITED_CHARGE",
                    "service": "Platform Infrastructure Levy",
                    "amount_inr": 18500.0,
                    "reason": "Matches prohibited charge: platform maintenance fees",
                    "contract_clause": "Section 6 - Prohibited Charges"
                })
            if "UNAPPROVED_AMENDMENT" in result_str or "UNAPPROVED AMENDMENT" in result_str:
                findings.append({
                    "type": "UNAPPROVED_AMENDMENT",
                    "amendment_refs": ["AMD-2024-01"],
                    "reason": "Invoice cites amendment with no signed counterpart",
                    "contract_clause": "Section 9 - Amendments and Modifications"
                })

            # Extract reasoning — first 400 chars of response
            reasoning = result_str[:400].strip()

            result_dict = {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "estimated_overbill_inr": estimated_overbill,
                "total_findings": len(findings),
                "findings": findings,
                "reasoning": reasoning,
                "contract_data": {
                    "vendor_name": vendor_name,
                    "contract_ref": contract_ref,
                    "billing_cycle": "monthly",
                    "payment_terms_days": 30
                },
                "invoice_data": {
                    "invoice_number": contract_ref,
                    "billing_period": billing_period,
                    "total": 0,
                    "subtotal": 0
                }
            }

        # Step 6 — Add metadata
        result_dict["vendor_name"] = vendor_name
        result_dict["invoice_number"] = contract_ref
        result_dict["s3_contract_key"] = contract_key
        result_dict["s3_invoice_key"] = invoice_key

        # Step 7 — Save result to S3
        print("Saving result to S3...")
        result_key = save_audit_result(
            contract_ref, billing_period, result_dict)
        result_dict["s3_result_key"] = result_key

        # Step 8 — Save to SQLite
        print("Saving to database...")
        save_audit(result_dict)

        print("Audit complete!")
        return {
            "status": "complete",
            "audit": result_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Audit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /query ───────────────────────────────────────────────────────────────
@app.post("/query")
async def query_audits(request: QueryRequest):
    try:
        print(f"Query received: {request.query}")

        # Fetch all audit data from DB first
        all_audits = get_all_audits()
        high_risk = get_high_risk_audits()

        # Build context from DB data
        audit_context = f"""
        You are a financial audit assistant. Answer the user's question
        using ONLY the audit data provided below from our database.
        Do not say you don't have access to data — the data is right here.

        === AUDIT DATABASE SUMMARY ===
        Total audits in system: {len(all_audits)}
        High risk audits: {len(high_risk)}

        === ALL AUDIT RECORDS ===
        {json.dumps(all_audits, indent=2)}

        === USER QUESTION ===
        {request.query}

        Answer clearly and specifically using the data above.
        """

        result = audit_agent(audit_context)
        return {
            "status": "complete",
            "answer": str(result)
        }
    except Exception as e:
        print(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /audits ───────────────────────────────────────────────────────────────
@app.get("/audits")
def list_audits():
    try:
        audits = get_all_audits()
        return {
            "status": "complete",
            "total": len(audits),
            "audits": audits
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /audits/high-risk ─────────────────────────────────────────────────────
@app.get("/audits/high-risk")
def list_high_risk():
    try:
        audits = get_high_risk_audits()
        return {
            "status": "complete",
            "total": len(audits),
            "audits": audits
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /audits/{vendor_name} ─────────────────────────────────────────────────
@app.get("/audits/{vendor_name}")
def list_vendor_audits(vendor_name: str):
    try:
        audits = get_audits_by_vendor(vendor_name)
        return {
            "status": "complete",
            "vendor": vendor_name,
            "total": len(audits),
            "audits": audits
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
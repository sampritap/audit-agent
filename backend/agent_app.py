import os
import json
from dotenv import load_dotenv
from bedrock_agentcore import BedrockAgentCoreApp
from parsers.pdf_parser import extract_text_from_bytes
from agent.audit_agent import audit_agent
from storage.s3_manager import download_pdf, save_audit_result
from db.crud import save_audit

load_dotenv()

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: dict) -> dict:
    """
    Two modes:
    1. Natural language query  → { "prompt": "..." }
    2. Full audit via S3 keys → { "contract_s3_key": "...", "invoice_s3_key": "..." }
    """
    try:
        # Mode 1 — Natural language query
        if "prompt" in payload:
            result = audit_agent(payload["prompt"])
            return {"result": str(result)}

        # Mode 2 — Full audit using S3 keys
        contract_s3_key = payload.get("contract_s3_key")
        invoice_s3_key = payload.get("invoice_s3_key")
        contract_ref = payload.get("contract_ref", "UNKNOWN")
        period = payload.get("period", "unknown")
        vendor_name = payload.get("vendor_name", "Unknown")

        if not contract_s3_key or not invoice_s3_key:
            return {"error": "Missing contract_s3_key or invoice_s3_key"}

        # Download PDFs from S3
        print("Downloading PDFs from S3...")
        contract_bytes = download_pdf(contract_s3_key)
        invoice_bytes = download_pdf(invoice_s3_key)

        # Extract text
        contract_text = extract_text_from_bytes(contract_bytes)
        invoice_text = extract_text_from_bytes(invoice_bytes)

        # Run audit agent
        print("Running audit agent...")
        result = audit_agent(
            f"Audit this vendor invoice against the contract.\n\n"
            f"=== CONTRACT ===\n{contract_text}\n\n"
            f"=== INVOICE ===\n{invoice_text}"
        )

        result_dict = {
            "result": str(result),
            "vendor_name": vendor_name,
            "contract_ref": contract_ref,
            "period": period,
            "s3_contract_key": contract_s3_key,
            "s3_invoice_key": invoice_s3_key
        }

        # Save to S3 and DB
        save_audit_result(contract_ref, period, result_dict)
        save_audit(result_dict)

        return result_dict

    except Exception as e:
        print(f"AgentCore invoke error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    app.run(port=8081)

import os
from dotenv import load_dotenv
from strands import Agent
from strands.models import GeminiModel
from agent.tools.contract_extractor import extract_contract_terms
from agent.tools.invoice_extractor import extract_invoice_data
from agent.tools.drift_scorer import compute_drift_score

load_dotenv()

USE_LOCAL_MODE = os.getenv("USE_LOCAL_MODE", "false").lower() == "true"

if USE_LOCAL_MODE:
    print("⚠️  Audit agent running in LOCAL MODE - using mock data")
    
    def audit_agent(prompt: str):
        """Local mode audit: directly calls tools with mock data."""
        print("Running local audit (no LLM)...")
        
        contract_data = extract_contract_terms("")
        invoice_data = extract_invoice_data("")
        drift_result = compute_drift_score(contract_data, invoice_data)
        
        return f"""
# Audit Complete

**Risk Score**: {drift_result['risk_score']}/100
**Risk Level**: {drift_result['risk_level']}
**Total Findings**: {drift_result['total_findings']}
**Estimated Overbill**: INR {drift_result['estimated_overbill_inr']:,.2f}

## Findings

{chr(10).join([f"- **{f['type']}**: {f.get('service', 'N/A')} - {f.get('reason', 'See details')} (Clause: {f.get('contract_clause', 'N/A')})" for f in drift_result['findings']])}

## Reasoning

{drift_result['reasoning']}

## Recommendation

Dispute these charges before payment. Request vendor to provide justification for price increases and prohibited charges.
"""

else:
    # ── Create Gemini Agent ───────────────────────────────────────────
    audit_agent = Agent(
        model=GeminiModel(
            model_id="gemini-1.5-pro",  # or "gemini-1.5-flash" (faster, cheaper)
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.0
        ),
        tools=[
            extract_contract_terms,
            extract_invoice_data,
            compute_drift_score
        ],
        system_prompt="""
        You are an autonomous financial audit agent for detecting vendor
        invoice overbilling and contract drift.

        When given contract and invoice text, you MUST follow this
        exact sequence every single time:

        STEP 1 — Call extract_contract_terms() with the full contract text
        STEP 2 — Call extract_invoice_data() with the full invoice text
        STEP 3 — Call compute_drift_score() passing both results

        Return a final audit report with:
        - Risk score and risk level (HIGH/MEDIUM/LOW)
        - Every finding with the exact contract clause it violates
        - Total estimated overbill amount in INR
        - A clear 2-sentence recommendation for the finance team
        """
    )

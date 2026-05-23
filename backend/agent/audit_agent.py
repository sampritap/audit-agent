import os
import boto3
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
from agent.tools.contract_extractor import extract_contract_terms
from agent.tools.invoice_extractor import extract_invoice_data
from agent.tools.drift_scorer import compute_drift_score

load_dotenv()

USE_LOCAL_MODE = os.getenv("USE_LOCAL_MODE", "false").lower() == "true"

if USE_LOCAL_MODE:
    print("⚠️  Audit agent running in LOCAL MODE - using mock data")
    
    # In local mode, create a simple function that calls tools directly
    def audit_agent(prompt: str):
        """
        Local mode audit: directly calls tools with mock data.
        Bypasses Bedrock entirely.
        """
        print("Running local audit (no Bedrock)...")
        
        # Extract contract and invoice from prompt (not used in local mode)
        contract_data = extract_contract_terms("")
        invoice_data = extract_invoice_data("")
        drift_result = compute_drift_score(contract_data, invoice_data)
        
        # Format response
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
    # ── Create boto3 session with credentials ────────────────────────────────────
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    )

    # ── Create the Strands Audit Agent ───────────────────────────────────────────
    audit_agent = Agent(
        model=BedrockModel(
            model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
            boto_session=session,
            temperature=0.0,
            streaming=True
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
        exact sequence every single time — never skip any step:

        STEP 1 — Call extract_contract_terms() with the full contract text
        STEP 2 — Call extract_invoice_data() with the full invoice text
        STEP 3 — Call compute_drift_score() passing both results from
                 Step 1 and Step 2 as arguments

        After all 3 steps complete, return a final audit report with:
        - Risk score and risk level (HIGH/MEDIUM/LOW)
        - Every finding with the exact contract clause it violates
        - Total estimated overbill amount in INR
        - A clear 2-sentence recommendation for the finance team
        - Which charges should be disputed before payment

        Rules:
        - Never guess or make up numbers
        - Always cite the exact contract clause for each finding
        - Always complete all 3 steps before returning results
        - If a step fails, report the error clearly
        """,
        #max_parallel_tools=1
    )
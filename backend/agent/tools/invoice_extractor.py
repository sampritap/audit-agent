from strands import tool, Agent
from strands.models import BedrockModel
import json
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

USE_LOCAL_MODE = os.getenv("USE_LOCAL_MODE", "false").lower() == "true"

if USE_LOCAL_MODE:
    from .mock_responses import MOCK_INVOICE_DATA

@tool
def extract_invoice_data(invoice_text: str) -> dict:
    """
    Extracts structured billing data from vendor invoice text.
    Returns all line items with unit prices, quantities, and amounts.
    Also captures amendment references and vendor notes.
    Must be called AFTER extract_contract_terms.
    """
    
    # LOCAL MODE: Return mock data
    if USE_LOCAL_MODE:
        print("✓ Using mock invoice data (LOCAL MODE)")
        return MOCK_INVOICE_DATA
    
    try:
        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        )

        extractor = Agent(
            model=BedrockModel(
                model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
                boto_session=session,
                temperature=0.0
            ),
            system_prompt="You are an invoice data extraction specialist. Return ONLY valid JSON. No explanation, no markdown."
        )

        prompt = f"""
        Extract all billing data from this invoice.
        Return ONLY this exact JSON structure, nothing else:
        {{
            "vendor_name": "string",
            "invoice_number": "string",
            "invoice_date": "string",
            "billing_period": "string",
            "line_items": [
                {{
                    "description": "string",
                    "unit": "string",
                    "quantity": 0.0,
                    "unit_price": 0.0,
                    "amount": 0.0,
                    "looks_unusual": false
                }}
            ],
            "subtotal": 0.0,
            "tax_amount": 0.0,
            "total": 0.0,
            "amendment_refs": ["string"],
            "vendor_notes": ["string"],
            "confidence": 0.0
        }}

        INVOICE TEXT:
        {invoice_text[:10000]}
        """

        response = str(extractor(prompt))

        # Extract JSON reliably
        start = response.find("{")
        end = response.rfind("}") + 1
        clean = response[start:end]
        return json.loads(clean)

    except Exception as e:
        print(f"Invoice extraction error: {e}")
        return {
            "vendor_name": "", "invoice_number": "",
            "invoice_date": "", "billing_period": "",
            "line_items": [], "subtotal": 0.0,
            "tax_amount": 0.0, "total": 0.0,
            "amendment_refs": [], "vendor_notes": [],
            "confidence": 0.0
        }
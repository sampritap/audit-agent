from strands import tool, Agent
from strands.models import BedrockModel
import json
import os
import boto3
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

USE_LOCAL_MODE = os.getenv("USE_LOCAL_MODE", "false").lower() == "true"

if USE_LOCAL_MODE:
    from .mock_responses import MOCK_CONTRACT_DATA

@tool
def extract_contract_terms(contract_text: str) -> dict:
    """
    Extracts structured billing terms from vendor contract text.
    Returns unit prices, volume caps, payment terms, prohibited charges,
    and amendment references. Must be called first before invoice extraction.
    """
    
    # LOCAL MODE: Return mock data
    if USE_LOCAL_MODE:
        print("✓ Using mock contract data (LOCAL MODE)")
        return MOCK_CONTRACT_DATA
    
    try:
        # Explicitly create boto3 session with credentials from .env
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
                #region_name=os.getenv("AWS_DEFAULT_REGION", "us-west-2"),
                temperature=0.0
            ),
            system_prompt="You are a contract analysis specialist. Return ONLY valid JSON. No explanation, no markdown."
        )

        prompt = f"""
        Extract all billing terms from this contract.
        Return ONLY this exact JSON structure, nothing else:
        {{
            "vendor_name": "string",
            "contract_ref": "string",
            "effective_date": "string",
            "expiry_date": "string",
            "unit_prices": [
                {{"service": "string", "unit": "string", "price": 0.0}}
            ],
            "volume_caps": [
                {{"service": "string", "cap": 0.0, "unit": "string", "overage_rate": 0.0}}
            ],
            "billing_cycle": "string",
            "payment_terms_days": 0,
            "prohibited_charges": ["string"],
            "amendment_refs": ["string"],
            "confidence": 0.0
        }}

        CONTRACT TEXT:
        {contract_text[:10000]}
        """

        response = str(extractor(prompt))

        # Extract JSON from response
        start = response.find("{")
        end = response.rfind("}") + 1
        clean = response[start:end]
        return json.loads(clean)

    except Exception as e:
        print(f"Contract extraction error: {e}")
        return {
            "vendor_name": "", "contract_ref": "",
            "effective_date": "", "expiry_date": "",
            "unit_prices": [], "volume_caps": [],
            "billing_cycle": "", "payment_terms_days": 0,
            "prohibited_charges": [], "amendment_refs": [],
            "confidence": 0.0
        }





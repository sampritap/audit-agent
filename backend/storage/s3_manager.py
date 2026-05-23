import boto3
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BUCKET = "axiom-audit-documents"
USE_LOCAL_MODE = os.getenv("USE_LOCAL_MODE", "false").lower() == "true"

# Local storage directory
LOCAL_STORAGE_DIR = Path(__file__).parent.parent / "local_storage"
LOCAL_STORAGE_DIR.mkdir(exist_ok=True)

if USE_LOCAL_MODE:
    print("⚠️  Running in LOCAL MODE - S3 disabled, using local storage")

def get_s3_client():
    """Create S3 client with credentials from .env"""
    if USE_LOCAL_MODE:
        return None
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    )

def upload_contract(file_bytes: bytes, vendor_name: str, contract_ref: str) -> str:
    """
    Upload contract PDF to S3 or local storage.
    Returns the S3 key or local path where file was stored.
    """
    key = f"contracts/{contract_ref}/original/{vendor_name}_contract.pdf"
    
    if USE_LOCAL_MODE:
        # Save locally
        local_path = LOCAL_STORAGE_DIR / key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(file_bytes)
        print(f"✓ Contract saved locally: {local_path}")
        return key
    
    try:
        s3 = get_s3_client()
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=file_bytes,
            ContentType="application/pdf",
            Metadata={
                "vendor": vendor_name,
                "contract_ref": contract_ref,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        )
        print(f"Contract uploaded to S3: {key}")
        return key
    except Exception as e:
        print(f"S3 upload contract error: {e}")
        return ""

def upload_invoice(file_bytes: bytes, vendor_name: str, period: str) -> str:
    """
    Upload invoice PDF to S3 or local storage.
    Returns the S3 key or local path where file was stored.
    """
    key = f"invoices/{vendor_name}/{period}/{vendor_name}_invoice_{period}.pdf"
    
    if USE_LOCAL_MODE:
        # Save locally
        local_path = LOCAL_STORAGE_DIR / key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(file_bytes)
        print(f"✓ Invoice saved locally: {local_path}")
        return key
    
    try:
        s3 = get_s3_client()
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=file_bytes,
            ContentType="application/pdf",
            Metadata={
                "vendor": vendor_name,
                "period": period,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        )
        print(f"Invoice uploaded to S3: {key}")
        return key
    except Exception as e:
        print(f"S3 upload invoice error: {e}")
        return ""

def download_pdf(s3_key: str) -> bytes:
    """
    Download PDF bytes from S3 or local storage using key.
    """
    if USE_LOCAL_MODE:
        local_path = LOCAL_STORAGE_DIR / s3_key
        if local_path.exists():
            return local_path.read_bytes()
        return b""
    
    try:
        s3 = get_s3_client()
        response = s3.get_object(Bucket=BUCKET, Key=s3_key)
        return response["Body"].read()
    except Exception as e:
        print(f"S3 download error: {e}")
        return b""

def save_audit_result(contract_ref: str, period: str, result_dict: dict) -> str:
    """
    Save audit result JSON to S3 or local storage.
    Returns the S3 key or local path where result was stored.
    """
    key = f"audit-results/{contract_ref}/{period}/audit_result.json"
    
    if USE_LOCAL_MODE:
        # Save locally
        local_path = LOCAL_STORAGE_DIR / key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(json.dumps(result_dict, indent=2))
        print(f"✓ Audit result saved locally: {local_path}")
        return key
    
    try:
        s3 = get_s3_client()
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=json.dumps(result_dict, indent=2),
            ContentType="application/json",
            Metadata={
                "contract_ref": contract_ref,
                "period": period,
                "saved_at": datetime.utcnow().isoformat()
            }
        )
        print(f"Audit result saved to S3: {key}")
        return key
    except Exception as e:
        print(f"S3 save audit error: {e}")
        return ""

def list_vendor_invoices(vendor_name: str) -> list:
    """
    List all invoice S3 keys or local paths for a vendor.
    """
    if USE_LOCAL_MODE:
        invoice_dir = LOCAL_STORAGE_DIR / "invoices" / vendor_name
        if invoice_dir.exists():
            return [str(p.relative_to(LOCAL_STORAGE_DIR)) for p in invoice_dir.rglob("*.pdf")]
        return []
    
    try:
        s3 = get_s3_client()
        response = s3.list_objects_v2(
            Bucket=BUCKET,
            Prefix=f"invoices/{vendor_name}/"
        )
        return [obj["Key"] for obj in response.get("Contents", [])]
    except Exception as e:
        print(f"S3 list error: {e}")
        return []

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Check if credentials loaded
print("Region:", os.getenv("AWS_DEFAULT_REGION"))
print("Key ID:", os.getenv("AWS_ACCESS_KEY_ID", "NOT FOUND")[:10] + "...")
print("Secret:", "SET" if os.getenv("AWS_SECRET_ACCESS_KEY") else "NOT FOUND")
print("Token:", "SET" if os.getenv("AWS_SESSION_TOKEN") else "NOT FOUND")

# Test actual AWS connection
import boto3
try:
    sts = boto3.client(
        "sts",
        region_name=os.getenv("AWS_DEFAULT_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN")
    )
    identity = sts.get_caller_identity()
    print("\n✅ AWS Connection SUCCESS!")
    print("Account:", identity["Account"])
    print("ARN:", identity["Arn"])
except Exception as e:
    print("\n❌ AWS Connection FAILED:", e)

# Test Bedrock access
try:
    bedrock = boto3.client(
        "bedrock",
        region_name=os.getenv("AWS_DEFAULT_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN")
    )
    models = bedrock.list_foundation_models()
    claude_models = [
        m["modelId"] for m in models["modelSummaries"]
        if "claude" in m["modelId"].lower()
    ]
    print("\n✅ Bedrock Access SUCCESS!")
    print("Available Claude models:")
    for m in claude_models:
        print(" -", m)
except Exception as e:
    print("\n❌ Bedrock Access FAILED:", e)
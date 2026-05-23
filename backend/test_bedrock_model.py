"""
Test if a specific Bedrock model works with your credentials.
"""
import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Models to try (from most to least likely to work)
MODELS_TO_TRY = [
    "amazon.titan-text-lite-v1",
    "amazon.titan-text-express-v1",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "meta.llama3-8b-instruct-v1:0",
    "mistral.mistral-7b-instruct-v0:2",
]

def test_model(model_id):
    """Test if a model is accessible."""
    try:
        bedrock_runtime = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        )
        
        # Simple test prompt
        if "titan" in model_id:
            # Titan format
            body = json.dumps({
                "inputText": "Say 'test successful' if you can read this.",
                "textGenerationConfig": {
                    "maxTokenCount": 50,
                    "temperature": 0
                }
            })
        elif "claude" in model_id:
            # Claude format
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 50,
                "messages": [
                    {"role": "user", "content": "Say 'test successful' if you can read this."}
                ]
            })
        else:
            # Generic format
            body = json.dumps({
                "prompt": "Say 'test successful' if you can read this.",
                "max_gen_len": 50,
                "temperature": 0
            })
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body
        )
        
        print(f"✓ {model_id} - WORKS!")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "AccessDeniedException" in error_msg:
            print(f"✗ {model_id} - Access Denied")
        elif "ValidationException" in error_msg:
            print(f"? {model_id} - Model not available in region")
        else:
            print(f"✗ {model_id} - Error: {error_msg[:100]}")
        return False

if __name__ == "__main__":
    print("Testing Bedrock models...\n")
    print("=" * 80)
    
    working_models = []
    
    for model_id in MODELS_TO_TRY:
        if test_model(model_id):
            working_models.append(model_id)
    
    print("\n" + "=" * 80)
    
    if working_models:
        print(f"\n✓ Found {len(working_models)} working model(s):")
        for model in working_models:
            print(f"  • {model}")
        print(f"\nUpdate your code to use: {working_models[0]}")
    else:
        print("\n✗ No Bedrock models are accessible with your credentials")
        print("\nYour AWS account has restricted Bedrock access.")
        print("Recommendation: Use LOCAL_MODE=true or switch to Google Gemini (FREE)")

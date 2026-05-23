"""
Check which Bedrock models are available in your AWS account.
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def check_bedrock_access():
    """Test Bedrock access and list available models."""
    
    try:
        # Create Bedrock client
        bedrock = boto3.client(
            'bedrock',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        )
        
        print("✓ Bedrock client created successfully")
        print("\nAttempting to list foundation models...\n")
        
        # Try to list models
        response = bedrock.list_foundation_models()
        
        print(f"✓ Found {len(response['modelSummaries'])} models\n")
        print("Available models:")
        print("-" * 80)
        
        for model in response['modelSummaries']:
            model_id = model['modelId']
            model_name = model.get('modelName', 'N/A')
            provider = model.get('providerName', 'N/A')
            
            # Check if it's a text model (good for our use case)
            input_modalities = model.get('inputModalities', [])
            output_modalities = model.get('outputModalities', [])
            
            if 'TEXT' in input_modalities and 'TEXT' in output_modalities:
                print(f"✓ {model_id}")
                print(f"  Provider: {provider}")
                print(f"  Name: {model_name}")
                print()
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Bedrock access denied: {error_msg}\n")
        
        if "AccessDeniedException" in error_msg or "explicit deny" in error_msg:
            print("=" * 80)
            print("DIAGNOSIS: Your AWS account has an EXPLICIT DENY policy")
            print("=" * 80)
            print("\nThis means:")
            print("• Your IAM role (WSParticipantRole) is blocked from using Bedrock")
            print("• This is common in AWS Academy/Learning environments")
            print("• Even if you had permissions elsewhere, the deny overrides everything")
            print("\nYour options:")
            print("1. Use LOCAL_MODE=true (already configured)")
            print("2. Switch to OpenAI, Anthropic, or Google Gemini (see alternatives)")
            print("3. Contact your AWS administrator to remove the deny policy")
            print("4. Use a different AWS account without restrictions")
            print("\nRecommendation: Use Google Gemini (FREE tier available)")
            print("Get API key at: https://ai.google.dev/")
        
        return False

if __name__ == "__main__":
    print("Checking AWS Bedrock access...\n")
    check_bedrock_access()

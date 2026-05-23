"""
Check your IAM permissions to understand what's blocked.
"""
import boto3
import json
from dotenv import load_dotenv
import os

load_dotenv()

def check_permissions():
    """Check what IAM permissions you have."""
    
    try:
        # Get current identity
        sts = boto3.client(
            'sts',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        )
        
        identity = sts.get_caller_identity()
        
        print("=" * 80)
        print("YOUR AWS IDENTITY")
        print("=" * 80)
        print(f"Account: {identity['Account']}")
        print(f"User ARN: {identity['Arn']}")
        print(f"User ID: {identity['UserId']}")
        print()
        
        # Extract role name from ARN
        arn = identity['Arn']
        if 'assumed-role' in arn:
            role_name = arn.split('/')[-2]
            print(f"Role Name: {role_name}")
            print()
            
            # Try to get role policies (might fail if no permission)
            try:
                iam = boto3.client(
                    'iam',
                    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
                    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
                )
                
                # List attached policies
                policies = iam.list_attached_role_policies(RoleName=role_name)
                
                print("=" * 80)
                print("ATTACHED IAM POLICIES")
                print("=" * 80)
                for policy in policies['AttachedPolicies']:
                    print(f"• {policy['PolicyName']}")
                    print(f"  ARN: {policy['PolicyArn']}")
                print()
                
            except Exception as e:
                print("✗ Cannot read IAM policies (permission denied)")
                print(f"  Error: {e}")
                print()
        
        # Test specific Bedrock actions
        print("=" * 80)
        print("TESTING BEDROCK PERMISSIONS")
        print("=" * 80)
        
        bedrock_actions = [
            ("List Models", "bedrock", "list_foundation_models"),
            ("Invoke Model", "bedrock-runtime", "invoke_model"),
            ("Invoke Streaming", "bedrock-runtime", "invoke_model_with_response_stream"),
        ]
        
        for action_name, service, method in bedrock_actions:
            try:
                client = boto3.client(
                    service,
                    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
                    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
                )
                
                if method == "list_foundation_models":
                    client.list_foundation_models()
                    print(f"✓ {action_name}: ALLOWED")
                else:
                    print(f"? {action_name}: Cannot test without model ID")
                    
            except Exception as e:
                error_msg = str(e)
                if "AccessDeniedException" in error_msg:
                    print(f"✗ {action_name}: DENIED")
                    if "explicit deny" in error_msg:
                        print(f"  → Blocked by explicit deny policy")
                elif "ValidationException" in error_msg:
                    print(f"✓ {action_name}: ALLOWED (validation error is OK)")
                else:
                    print(f"? {action_name}: {error_msg[:80]}")
        
        print()
        print("=" * 80)
        print("DIAGNOSIS")
        print("=" * 80)
        print("If you see 'explicit deny' above, your AWS administrator needs to:")
        print("1. Go to AWS IAM Console")
        print("2. Find role: WSParticipantRole")
        print("3. Find policy: policy-0")
        print("4. Edit the policy to remove Bedrock deny statements")
        print()
        print("OR you can:")
        print("• Use LOCAL_MODE=true (no AWS needed)")
        print("• Switch to Google Gemini, OpenAI, or Anthropic (no AWS needed)")
        
    except Exception as e:
        print(f"✗ Error checking permissions: {e}")

if __name__ == "__main__":
    check_permissions()

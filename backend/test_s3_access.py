"""
Test S3 access and create bucket if needed.
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = "audit-documents-triumph"

def test_s3_access():
    """Test if we can access S3 and the bucket."""
    
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        )
        
        print("✓ S3 client created successfully\n")
        
        # Check if bucket exists
        print(f"Checking if bucket '{BUCKET_NAME}' exists...")
        try:
            s3.head_bucket(Bucket=BUCKET_NAME)
            print(f"✓ Bucket '{BUCKET_NAME}' exists and is accessible\n")
            
            # List some objects
            response = s3.list_objects_v2(Bucket=BUCKET_NAME, MaxKeys=5)
            if 'Contents' in response:
                print(f"Found {len(response['Contents'])} objects in bucket:")
                for obj in response['Contents']:
                    print(f"  • {obj['Key']}")
            else:
                print("Bucket is empty (ready for uploads)")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "NoSuchBucket" in error_msg:
                print(f"✗ Bucket '{BUCKET_NAME}' does not exist\n")
                
                # Try to create it
                print("Attempting to create bucket...")
                try:
                    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
                    if region == "us-east-1":
                        s3.create_bucket(Bucket=BUCKET_NAME)
                    else:
                        s3.create_bucket(
                            Bucket=BUCKET_NAME,
                            CreateBucketConfiguration={'LocationConstraint': region}
                        )
                    print(f"✓ Bucket '{BUCKET_NAME}' created successfully!")
                    return True
                except Exception as create_error:
                    print(f"✗ Cannot create bucket: {create_error}")
                    print("\nYou need to:")
                    print("1. Go to AWS S3 Console")
                    print(f"2. Create bucket: {BUCKET_NAME}")
                    print("3. Or use a different bucket name in s3_manager.py")
                    return False
            elif "403" in error_msg or "AccessDenied" in error_msg:
                print(f"✗ Access denied to bucket '{BUCKET_NAME}'")
                print("\nYour IAM role needs these S3 permissions:")
                print("  • s3:ListBucket")
                print("  • s3:GetObject")
                print("  • s3:PutObject")
                return False
            else:
                print(f"✗ Error: {error_msg}")
                return False
                
    except Exception as e:
        print(f"✗ S3 access error: {e}")
        
        if "ExpiredToken" in str(e):
            print("\n⚠️  Your AWS credentials have expired!")
            print("Get fresh credentials from AWS Academy/Learner Lab")
        elif "InvalidAccessKeyId" in str(e):
            print("\n⚠️  Invalid AWS credentials!")
            print("Check your .env file has correct AWS_ACCESS_KEY_ID")
        
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("TESTING S3 ACCESS")
    print("=" * 80)
    print()
    
    if test_s3_access():
        print("\n" + "=" * 80)
        print("✓ S3 is ready! You can now upload files.")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("✗ S3 access failed. Fix the issues above.")
        print("=" * 80)

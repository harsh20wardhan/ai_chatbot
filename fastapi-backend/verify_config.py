#!/usr/bin/env python3

"""
Configuration Verification Script

Quick script to verify that all environment variables are properly configured
for the cloud services setup.
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Please copy .env.example to .env and configure it")
        return False
    
    print("✅ .env file found")
    
    # Read .env file
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    required_vars = [
        'QDRANT_URL',
        'QDRANT_API_KEY',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION',
        'BEDROCK_RAG_MODEL',
        'BEDROCK_EMBEDDING_MODEL',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY',
        'SUPABASE_DB_HOST',
        'SUPABASE_DB_USER',
        'SUPABASE_DB_PASSWORD'
    ]
    
    missing_vars = []
    configured_vars = []
    
    for var in required_vars:
        if f"{var}=" in env_content and not f"{var}=your-" in env_content and not f"{var}=\n" in env_content:
            configured_vars.append(var)
        else:
            missing_vars.append(var)
    
    print(f"\n📊 Configuration Status:")
    print(f"   Configured: {len(configured_vars)}/{len(required_vars)}")
    
    if configured_vars:
        print("\n✅ Configured variables:")
        for var in configured_vars:
            print(f"   - {var}")
    
    if missing_vars:
        print("\n❌ Missing or unconfigured variables:")
        for var in missing_vars:
            print(f"   - {var}")
    
    return len(missing_vars) == 0

def check_cloud_services_config():
    """Check specific cloud services configuration"""
    print("\n🔍 Checking cloud services configuration...")
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment")
    
    # Check Qdrant Cloud URL
    qdrant_url = os.getenv('QDRANT_URL', '')
    if 'cloud.qdrant.io' in qdrant_url:
        print("✅ Qdrant Cloud URL configured")
    else:
        print("❌ Qdrant Cloud URL not configured or using local instance")
    
    # Check Bedrock models
    rag_model = os.getenv('BEDROCK_RAG_MODEL', '')
    embedding_model = os.getenv('BEDROCK_EMBEDDING_MODEL', '')
    
    if rag_model == 'openai.gpt-oss-20b-1:0':
        print("✅ Bedrock RAG model configured correctly")
    else:
        print(f"❌ Bedrock RAG model not configured correctly: {rag_model}")
    
    if embedding_model == 'amazon.titan-embed-text-v2:0':
        print("✅ Bedrock embedding model configured correctly")
    else:
        print(f"❌ Bedrock embedding model not configured correctly: {embedding_model}")
    
    # Check AWS region
    aws_region = os.getenv('AWS_REGION', '')
    if aws_region:
        print(f"✅ AWS region configured: {aws_region}")
    else:
        print("❌ AWS region not configured")
    
    # Check AWS credentials
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID', '')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    
    if aws_access_key and aws_access_key != 'your-aws-access-key-id':
        print("✅ AWS access key configured")
    else:
        print("❌ AWS access key not configured")
    
    if aws_secret_key and aws_secret_key != 'your-aws-secret-access-key':
        print("✅ AWS secret key configured")
    else:
        print("❌ AWS secret key not configured")

def main():
    """Main verification function"""
    print("=" * 50)
    print("FastAPI Backend Configuration Verification")
    print("=" * 50)
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded from .env")
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment")
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
    
    # Check .env file
    env_ok = check_env_file()
    
    # Check cloud services configuration
    check_cloud_services_config()
    
    print("\n" + "=" * 50)
    if env_ok:
        print("🎉 Configuration looks good!")
        print("\nNext steps:")
        print("1. Run: python test_cloud_services.py")
        print("2. If tests pass, start the backend: ./start.sh")
    else:
        print("⚠️  Configuration needs attention")
        print("\nPlease:")
        print("1. Copy .env.example to .env")
        print("2. Fill in all required variables")
        print("3. Run this script again")
    
    print("=" * 50)
    
    return env_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
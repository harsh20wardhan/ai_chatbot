#!/usr/bin/env python3
"""
Test runner for FastAPI backend

This script runs the test suite and provides a comprehensive report
on API compatibility and functionality.
"""

import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run the test suite"""
    
    print("=" * 80)
    print("FastAPI Backend Test Suite")
    print("=" * 80)
    print()
    
    # Change to the fastapi-backend directory
    os.chdir(Path(__file__).parent)
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest is not installed. Please install it with:")
        print("   pip install pytest pytest-asyncio pytest-httpx")
        return False
    
    # Run different test categories
    test_categories = [
        ("Health Checks", "tests/test_health.py"),
        ("API Compatibility", "tests/test_api_compatibility.py"),
        ("Middleware", "tests/test_middleware.py"),
        ("Services", "tests/test_services.py")
    ]
    
    all_passed = True
    results = {}
    
    for category, test_file in test_categories:
        print(f"Running {category} tests...")
        print("-" * 40)
        
        try:
            # Run pytest for this category
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, 
                "-v", 
                "--tb=short",
                "--no-header"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {category}: PASSED")
                results[category] = "PASSED"
            else:
                print(f"❌ {category}: FAILED")
                results[category] = "FAILED"
                all_passed = False
                
                # Show error details
                if result.stdout:
                    print("STDOUT:")
                    print(result.stdout)
                if result.stderr:
                    print("STDERR:")
                    print(result.stderr)
                    
        except Exception as e:
            print(f"❌ {category}: ERROR - {e}")
            results[category] = f"ERROR: {e}"
            all_passed = False
        
        print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for category, result in results.items():
        status_icon = "✅" if result == "PASSED" else "❌"
        print(f"{status_icon} {category}: {result}")
    
    print()
    if all_passed:
        print("🎉 All tests passed! The FastAPI backend is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False

def run_compatibility_check():
    """Run a quick compatibility check"""
    
    print("=" * 80)
    print("FastAPI Backend Compatibility Check")
    print("=" * 80)
    print()
    
    # Check imports
    print("Checking imports...")
    
    imports_to_check = [
        ("FastAPI", "fastapi"),
        ("Uvicorn", "uvicorn"),
        ("AsyncPG", "asyncpg"),
        ("Supabase", "supabase"),
        ("Qdrant Client", "qdrant_client"),
        ("Boto3", "boto3"),
        ("Pydantic", "pydantic"),
        ("HTTPX", "httpx")
    ]
    
    missing_imports = []
    
    for name, module in imports_to_check:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - Not installed")
            missing_imports.append(module)
    
    print()
    
    if missing_imports:
        print("Missing dependencies:")
        for module in missing_imports:
            print(f"  - {module}")
        print()
        print("Install missing dependencies with:")
        print(f"  pip install {' '.join(missing_imports)}")
        return False
    
    # Check configuration
    print("Checking configuration...")
    
    try:
        from config.settings import settings
        
        required_settings = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "QDRANT_URL"
        ]
        
        missing_settings = []
        
        for setting in required_settings:
            if hasattr(settings, setting) and getattr(settings, setting):
                print(f"✅ {setting}")
            else:
                print(f"❌ {setting} - Not configured")
                missing_settings.append(setting)
        
        if missing_settings:
            print()
            print("Missing configuration:")
            for setting in missing_settings:
                print(f"  - {setting}")
            print()
            print("Please check your .env file.")
            return False
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    print()
    print("✅ All compatibility checks passed!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        success = run_compatibility_check()
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)
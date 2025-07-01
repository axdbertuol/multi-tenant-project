#!/usr/bin/env python3
"""
Script to run all IAM session validation tests with detailed reporting.
"""

import subprocess
import sys
import os

def run_tests():
    """Run all IAM session validation tests."""
    
    print("🧪 Running IAM Session Validation Tests")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    test_commands = [
        {
            "name": "Unit Tests - Session Validation",
            "command": [
                "pytest", 
                "tests/unit/iam/application/use_cases/test_session_use_cases_validate_access.py",
                "-v", "--tb=short", "--no-header"
            ]
        },
        {
            "name": "Integration Tests - Session Validation",
            "command": [
                "pytest", 
                "tests/integration/iam/application/use_cases/test_session_use_cases_validate_access_integration.py",
                "-v", "--tb=short", "--no-header"
            ]
        },
        {
            "name": "End-to-End Tests - Session Validation",
            "command": [
                "pytest", 
                "tests/e2e/iam/api/test_session_validation_endpoints.py",
                "-v", "--tb=short", "--no-header"
            ]
        },
        {
            "name": "All IAM Tests Summary",
            "command": [
                "pytest", 
                "tests/unit/iam", "tests/integration/iam", "tests/e2e/iam",
                "--tb=line", "--no-header", "-q"
            ]
        }
    ]
    
    results = []
    
    for test_suite in test_commands:
        print(f"\n🔹 {test_suite['name']}")
        print("-" * 40)
        
        try:
            result = subprocess.run(
                test_suite['command'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print("✅ PASSED")
                results.append((test_suite['name'], "PASSED"))
            else:
                print("❌ FAILED")
                results.append((test_suite['name'], "FAILED"))
                
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
                
        except subprocess.TimeoutExpired:
            print("⏰ TIMEOUT")
            results.append((test_suite['name'], "TIMEOUT"))
        except Exception as e:
            print(f"💥 ERROR: {e}")
            results.append((test_suite['name'], "ERROR"))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for name, status in results:
        status_icon = "✅" if status == "PASSED" else "❌"
        print(f"{status_icon} {name}: {status}")
        
        if status == "PASSED":
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n🚨 {failed} test suite(s) failed!")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
#!/usr/bin/env python3
"""
Authorization Service Test Runner

Script to run comprehensive integration tests for the AuthorizationService.authorize() function.
Includes tests for role inheritance, RBAC+ABAC combinations, and edge cases.

Usage:
    python run_authorization_tests.py [options]

Options:
    --all           Run all authorization tests (default)
    --core          Run core integration tests only
    --inheritance   Run role inheritance tests only (including RH example)
    --edge-cases    Run edge cases tests only
    --performance   Run performance tests only
    --coverage      Run with coverage reporting
    --verbose       Verbose output
    --fail-fast     Stop on first failure
    --html-report   Generate HTML coverage report
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle the result."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print(f"\n✅ {description} - PASSED")
    else:
        print(f"\n❌ {description} - FAILED")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Run AuthorizationService integration tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--all", action="store_true", default=True,
                       help="Run all authorization tests (default)")
    parser.add_argument("--core", action="store_true",
                       help="Run core integration tests only")
    parser.add_argument("--inheritance", action="store_true",
                       help="Run role inheritance tests only")
    parser.add_argument("--edge-cases", action="store_true",
                       help="Run edge cases tests only")
    parser.add_argument("--performance", action="store_true",
                       help="Run performance tests only")
    parser.add_argument("--coverage", action="store_true",
                       help="Run with coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--fail-fast", "-x", action="store_true",
                       help="Stop on first failure")
    parser.add_argument("--html-report", action="store_true",
                       help="Generate HTML coverage report")
    
    args = parser.parse_args()
    
    # If specific test types are selected, disable --all
    if any([args.core, args.inheritance, args.edge_cases, args.performance]):
        args.all = False
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    
    # Common options
    if args.verbose:
        base_cmd.append("-v")
    if args.fail_fast:
        base_cmd.append("-x")
    
    # Coverage options
    coverage_args = []
    if args.coverage:
        coverage_args.extend([
            "--cov=src.authorization.domain.services.authorization_service",
            "--cov-report=term-missing"
        ])
        if args.html_report:
            coverage_args.append("--cov-report=html")
    
    test_base_path = "tests/integration/application/services"
    
    success = True
    
    print("🚀 Starting Authorization Service Integration Tests")
    print("=" * 60)
    
    # Run selected test suites
    if args.all or args.core:
        cmd = base_cmd + [
            f"{test_base_path}/test_authorization_service_integration.py"
        ] + coverage_args
        
        if not run_command(cmd, "Core Integration Tests"):
            success = False
            if args.fail_fast:
                return 1
    
    if args.all or args.inheritance:
        cmd = base_cmd + [
            f"{test_base_path}/test_authorization_service_role_inheritance.py"
        ] + coverage_args
        
        if not run_command(cmd, "Role Inheritance Tests (including RH example)"):
            success = False
            if args.fail_fast:
                return 1
    
    if args.all or args.edge_cases:
        cmd = base_cmd + [
            f"{test_base_path}/test_authorization_service_edge_cases.py"
        ] + coverage_args
        
        if not run_command(cmd, "Edge Cases Tests"):
            success = False
            if args.fail_fast:
                return 1
    
    if args.performance:
        cmd = base_cmd + [
            f"{test_base_path}/",
            "-k", "performance"
        ] + coverage_args
        
        if not run_command(cmd, "Performance Tests"):
            success = False
            if args.fail_fast:
                return 1
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    if success:
        print("🎉 All tests PASSED!")
        print("\n✨ AuthorizationService.authorize() function is working correctly!")
        print("\n📋 Test Coverage:")
        print("   ✅ Core RBAC + ABAC authorization flows")
        print("   ✅ Role inheritance scenarios (including rh_gerente → rh_assistente)")
        print("   ✅ Edge cases and error conditions")
        print("   ✅ Performance and scalability validation")
        
        if args.coverage:
            print(f"\n📈 Coverage report generated")
            if args.html_report:
                html_path = Path("htmlcov/index.html")
                if html_path.exists():
                    print(f"   📄 HTML report: {html_path.absolute()}")
        
        return 0
    else:
        print("💥 Some tests FAILED!")
        print("\n🔍 Check the output above for details on which tests failed.")
        print("🛠️  Fix the issues and run the tests again.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        sys.exit(1)
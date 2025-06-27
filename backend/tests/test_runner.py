"""
Test runner script for the Sales Order Entry System backend.
"""
import pytest
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

def run_unit_tests():
    """Run unit tests."""
    print("Running unit tests...")
    exit_code = pytest.main([
        "tests/test_erp_services.py",
        "tests/test_embedding_services.py", 
        "tests/test_agents.py",
        "-v",
        "--tb=short",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov"
    ])
    return exit_code

def run_integration_tests():
    """Run integration tests."""
    print("Running integration tests...")
    exit_code = pytest.main([
        "tests/test_api_integration.py",
        "-v",
        "--tb=short"
    ])
    return exit_code

def run_all_tests():
    """Run all tests."""
    print("Running all tests...")
    exit_code = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov"
    ])
    return exit_code

def run_specific_test(test_file: str):
    """Run a specific test file."""
    print(f"Running tests from {test_file}...")
    exit_code = pytest.main([
        f"tests/{test_file}",
        "-v",
        "--tb=short"
    ])
    return exit_code

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests for Sales Order Entry System")
    parser.add_argument(
        "test_type", 
        choices=["unit", "integration", "all", "specific"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--file",
        help="Specific test file to run (when test_type is 'specific')"
    )
    
    args = parser.parse_args()
    
    if args.test_type == "unit":
        exit_code = run_unit_tests()
    elif args.test_type == "integration":
        exit_code = run_integration_tests()
    elif args.test_type == "all":
        exit_code = run_all_tests()
    elif args.test_type == "specific":
        if not args.file:
            print("Error: --file is required when test_type is 'specific'")
            sys.exit(1)
        exit_code = run_specific_test(args.file)
    
    sys.exit(exit_code)
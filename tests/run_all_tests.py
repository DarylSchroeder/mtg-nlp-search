#!/usr/bin/env python3
"""
Main test runner for MTG NLP Search
Replaces: run_tests.sh and consolidates all test execution
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout.strip():
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr.strip():
                print("STDERR:", result.stderr)
            if result.stdout.strip():
                print("STDOUT:", result.stdout)
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Run all tests in order"""
    print("🧪 MTG NLP Search - Comprehensive Test Suite")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    tests_passed = 0
    tests_total = 0
    
    # 1. Unit Tests
    print("\n🧠 UNIT TESTS")
    print("-" * 30)
    
    unit_tests = [
        ("python unit/test_nlp.py", "NLP Parsing Logic")
    ]
    
    for cmd, desc in unit_tests:
        tests_total += 1
        if run_command(cmd, desc):
            tests_passed += 1
    
    # 2. Integration Tests  
    print("\n🌐 INTEGRATION TESTS")
    print("-" * 30)
    
    integration_tests = [
        ("python integration/test_api.py", "API Integration")
    ]
    
    for cmd, desc in integration_tests:
        tests_total += 1
        if run_command(cmd, desc):
            tests_passed += 1
    
    # Final Results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print(f"   Passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"❌ {tests_total - tests_passed} TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())

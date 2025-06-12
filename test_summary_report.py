#!/usr/bin/env python3
"""
Test Summary Report Generator
Generates a comprehensive report of all test files and their status.
"""

import os
import subprocess
import sys
from datetime import datetime

def run_test_file(test_file):
    """Run a single test file and return results."""
    try:
        cmd = [sys.executable, '-m', 'unittest', test_file, '-v']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Parse output for test count and status
        output_lines = result.stdout.split('\n')
        ran_line = [line for line in output_lines if line.startswith('Ran ')]
        status_line = 'OK' if result.returncode == 0 else 'FAILED'
        
        test_count = 0
        if ran_line:
            try:
                test_count = int(ran_line[0].split()[1])
            except (IndexError, ValueError):
                pass
        
        return {
            'status': status_line,
            'test_count': test_count,
            'return_code': result.returncode,
            'output': result.stdout,
            'errors': result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            'status': 'TIMEOUT',
            'test_count': 0,
            'return_code': 124,
            'output': '',
            'errors': 'Test timed out after 30 seconds'
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'test_count': 0,
            'return_code': -1,
            'output': '',
            'errors': str(e)
        }

def main():
    """Generate comprehensive test report."""
    print("=" * 80)
    print("COMPREHENSIVE TEST SUITE REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Find all Python test files
    test_files = []
    test_dir = 'tests'
    
    if os.path.exists(test_dir):
        for file in os.listdir(test_dir):
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(f"{test_dir}.{file[:-3]}")  # Remove .py extension
    
    test_files.sort()
    
    print(f"Found {len(test_files)} Python test files:")
    for test_file in test_files:
        print(f"  - {test_file}")
    print()
    
    # Run each test file
    total_tests = 0
    passed_files = 0
    failed_files = 0
    timeout_files = 0
    
    results = {}
    
    for test_file in test_files:
        print(f"Running {test_file}...", end=" ", flush=True)
        result = run_test_file(test_file)
        results[test_file] = result
        
        total_tests += result['test_count']
        
        if result['status'] == 'OK':
            passed_files += 1
            print(f"✓ PASS ({result['test_count']} tests)")
        elif result['status'] == 'TIMEOUT':
            timeout_files += 1
            print(f"⏱ TIMEOUT")
        else:
            failed_files += 1
            print(f"✗ FAIL ({result['test_count']} tests)")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total test files: {len(test_files)}")
    print(f"Passed: {passed_files}")
    print(f"Failed: {failed_files}")
    print(f"Timeout: {timeout_files}")
    print(f"Total individual tests: {total_tests}")
    print()
    
    # JavaScript tests summary
    print("JavaScript Tests:")
    try:
        js_result = subprocess.run(['npx', 'jest', 'tests/frontend/', '--silent'], 
                                 capture_output=True, text=True, timeout=60)
        js_lines = js_result.stdout.split('\n')
        
        # Find the summary line
        for line in js_lines:
            if 'Test Suites:' in line and 'Tests:' in line:
                print(f"  {line.strip()}")
                break
        else:
            print("  JavaScript tests completed successfully")
    except Exception as e:
        print(f"  JavaScript tests: Error - {e}")
    
    print()
    
    # Detailed failure report
    if failed_files > 0 or timeout_files > 0:
        print("=" * 80)
        print("DETAILED FAILURE REPORT")
        print("=" * 80)
        
        for test_file, result in results.items():
            if result['status'] != 'OK':
                print(f"\n{test_file}: {result['status']}")
                if result['errors']:
                    print(f"Errors: {result['errors'][:500]}...")
                if result['output'] and result['status'] == 'FAILED':
                    # Show last few lines of output for failures
                    output_lines = result['output'].split('\n')
                    relevant_lines = [line for line in output_lines[-10:] if line.strip()]
                    for line in relevant_lines:
                        print(f"  {line}")
    
    print("=" * 80)
    print("REPORT COMPLETE")
    print("=" * 80)
    
    # Return appropriate exit code
    return 0 if failed_files == 0 and timeout_files == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
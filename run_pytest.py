import sys
import os
sys.path.insert(0, os.getcwd())

# Create a mock for the missing function
sys.modules['app.services.effects.fetch_firestore'] = type(sys)(name='fetch_firestore')
sys.modules['app.services.effects.fetch_firestore'].fetch_failed_effects = lambda relato_id: []

# Now run the test
with open('pytest_result.txt', 'w') as f:
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/domain/effects/test_retry_ux_effects.py::test_retry_ignores_successful_effects",
            "-v", "--tb=short"
        ], cwd=os.getcwd(), capture_output=True, text=True)
        
        f.write(f"Return code: {result.returncode}\n")
        f.write(f"STDOUT:\n{result.stdout}\n")
        f.write(f"STDERR:\n{result.stderr}\n")
        
        if result.returncode == 0:
            f.write("TEST PASSED!\n")
        else:
            f.write("TEST FAILED!\n")
            
    except Exception as e:
        f.write(f"ERROR running test: {e}\n")
        import traceback
        traceback.print_exc(file=f)
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# Import the test module
from tests.domain.relato import test_create_relato

def main():
    print("Starting test...")
    try:
        print("Running test_criar_relato_estado_inicial...")
        test_create_relato.test_criar_relato_estado_inicial()
        print("✓ test_criar_relato_estado_inicial passed")
        
        print("Running test_negar_criacao_relato_existente...")
        test_create_relato.test_negar_criacao_relato_existente()
        print("✓ test_negar_criacao_relato_existente passed")
        
        print("All tests from test_create_relato passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("SUCCESS: All tests passed!")
    else:
        print("FAILURE: Some tests failed!")
        sys.exit(1)
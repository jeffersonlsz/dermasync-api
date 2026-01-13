import sys
import os
sys.path.insert(0, os.getcwd())

with open('import_test_result.txt', 'w') as f:
    try:
        from app.domain.relato.effects import PersistRelatoEffect
        f.write('SUCCESS: Import worked\n')
        f.write(f'PersistRelatoEffect: {PersistRelatoEffect}\n')
    except ImportError as e:
        f.write(f'FAILED: {e}\n')
        import traceback
        f.write("Traceback:\n")
        traceback.print_exc(file=f)
    except Exception as e:
        f.write(f'OTHER ERROR: {e}\n')
        import traceback
        f.write("Traceback:\n")
        traceback.print_exc(file=f)
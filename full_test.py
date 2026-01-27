import sys
import os
sys.path.insert(0, os.getcwd())

with open('test_result.txt', 'w') as f:
    try:
        # Test the specific functionality mentioned in the requirements
        from app.domain.relato.effects import rebuild_effect_from_result
        from app.services.effects.result import EffectResult
        
        # Create a mock EffectResult to test the rebuild function
        mock_result = EffectResult.error(
            relato_id="test-123",
            effect_type="PERSIST_RELATO",
            error_message="Simulated error for test",
            metadata={
                'owner_id': 'owner123',
                'status': None,
                'conteudo': 'test content',
                'imagens': {},
                'effect_ref': 'test-ref'
            }
        )
        
        # Test rebuilding an effect
        effect = rebuild_effect_from_result(mock_result)
        f.write(f'SUCCESS: rebuild_effect_from_result worked, got: {type(effect).__name__}\n')
        
        # Also test that orchestrator can import effects
        from app.domain.relato.orchestrator import decide
        f.write('SUCCESS: Orchestrator import worked\n')
        
        # Test that retry functionality works
        from app.services.retry_relato import retry_failed_effects
        f.write('SUCCESS: retry_relato import worked\n')
        
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
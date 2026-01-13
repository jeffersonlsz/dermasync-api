import sys
import os
sys.path.insert(0, os.getcwd())

# Write results to a file instead of console due to Windows console issues
with open('circular_import_test_results.txt', 'w', encoding='utf-8') as f:
    # Test that the circular import issue is resolved
    f.write("Testing that the circular import issue is resolved...\n")

    # This was the original error: ImportError: cannot import name 'PersistRelatoEffect'
    # from partially initialized module 'app.domain.relato.effects'
    try:
        from app.domain.relato.effects import PersistRelatoEffect
        f.write("✅ Successfully imported PersistRelatoEffect from effects module\n")

        from app.domain.relato.effects import UploadImagesEffect
        f.write("✅ Successfully imported UploadImagesEffect from effects module\n")

        from app.domain.relato.effects import EnqueueProcessingEffect
        f.write("✅ Successfully imported EnqueueProcessingEffect from effects module\n")

        from app.domain.relato.effects import rebuild_effect_from_result
        f.write("✅ Successfully imported rebuild_effect_from_result from effects module\n")

        # Test that orchestrator can import effects without circular import
        from app.domain.relato.orchestrator import decide
        f.write("✅ Orchestrator can import effects without circular import\n")

        # Test that the rebuild function works
        from app.services.effects.result import EffectResult
        mock_result = EffectResult(
            relato_id="test-123",
            effect_type="PERSIST_RELATO",
            effect_ref="test-ref",
            success=False,
            metadata={'owner_id': 'owner123', 'status': None, 'conteudo': 'test content', 'imagens': {}}
        )

        effect = rebuild_effect_from_result(mock_result)
        f.write(f"✅ rebuild_effect_from_result works correctly: {type(effect).__name__}\n")

        f.write("\n🎉 SUCCESS: Circular import issue has been resolved!\n")
        f.write("✅ All imports work correctly\n")
        f.write("✅ Effects can be imported from the main effects module\n")
        f.write("✅ Orchestrator can import effects without issues\n")
        f.write("✅ Rebuild functionality works as expected\n")

    except ImportError as e:
        f.write(f"❌ FAILED: Import error still exists: {e}\n")
        import traceback
        traceback.print_exc(file=f)
    except Exception as e:
        f.write(f"❌ FAILED: Other error: {e}\n")
        import traceback
        traceback.print_exc(file=f)
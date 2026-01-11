import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_direct():
    try:
        # Import the necessary modules
        from app.domain.relato.orchestrator import decide
        from app.domain.relato.contracts import Actor, CreateRelato, ActorRole
        from app.domain.relato.states import RelatoStatus
        
        print("Testing creation from initial state...")
        actor = Actor(id="user-123", role=ActorRole.USER)
        command = CreateRelato(
            relato_id="relato-456",
            owner_id="user-123",
            conteudo="Relato de teste",
            imagens={"antes": [], "durante": [], "depois": []}
        )

        decision = decide(command=command, actor=actor, current_state=None)

        assert decision.allowed is True
        assert decision.reason is None
        assert decision.previous_state is None
        assert decision.next_state == RelatoStatus.DRAFT
        assert len(decision.effects) > 0  # Deve ter efeitos de persistência e upload
        print("✓ Creation from initial state test passed")
        
        print("Testing denial of creation when relato already exists...")
        decision = decide(command=command, actor=actor, current_state=RelatoStatus.DRAFT)

        assert decision.allowed is False
        assert decision.previous_state == RelatoStatus.DRAFT
        assert decision.next_state is None
        assert decision.effects == []  # Não deve ter efeitos quando negado
        assert decision.reason is not None  # Reason should not be None when denied
        print("✓ Denial of creation when relato exists test passed")
        
        print("All direct tests passed!")
        return True
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct()
    if success:
        print("SUCCESS: All direct tests passed!")
    else:
        print("FAILURE: Some tests failed!")
        sys.exit(1)
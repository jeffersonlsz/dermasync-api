#!/usr/bin/env python
"""Simple test runner to check if the domain tests pass."""

import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, '.')

# Import the test modules
from tests.domain.relato import test_create_relato
from tests.domain.relato import test_submit_relato
from tests.domain.relato import test_invalid_transitions
from tests.domain.relato import test_permissions

def run_tests():
    """Run all tests manually."""
    print("Running test_create_relato...")
    try:
        test_create_relato.test_criar_relato_estado_inicial()
        print("✓ test_criar_relato_estado_inicial passed")
        
        test_create_relato.test_negar_criacao_relato_existente()
        print("✓ test_negar_criacao_relato_existente passed")
    except Exception as e:
        print(f"✗ test_create_relato failed: {e}")
        return False
    
    print("\nRunning test_submit_relato...")
    try:
        test_submit_relato.test_submeter_relato_estado_draft()
        print("✓ test_submeter_relato_estado_draft passed")
        
        test_submit_relato.test_negar_submissao_estado_invalido()
        print("✓ test_negar_submissao_estado_invalido passed")
        
        test_submit_relato.test_negar_submissao_estado_processado()
        print("✓ test_negar_submissao_estado_processado passed")
        
        test_submit_relato.test_negar_submissao_estado_error()
        print("✓ test_negar_submissao_estado_error passed")
    except Exception as e:
        print(f"✗ test_submit_relato failed: {e}")
        return False
    
    print("\nRunning test_invalid_transitions...")
    try:
        test_invalid_transitions.test_negar_submissao_estado_error()
        print("✓ test_negar_submissao_estado_error passed")
        
        test_invalid_transitions.test_negar_submissao_estado_processado()
        print("✓ test_negar_submissao_estado_processado passed")
        
        test_invalid_transitions.test_negar_aprovacao_estado_draft()
        print("✓ test_negar_aprovacao_estado_draft passed")
        
        test_invalid_transitions.test_negar_aprovacao_estado_processing()
        print("✓ test_negar_aprovacao_estado_processing passed")
        
        test_invalid_transitions.test_negar_rejeicao_estado_draft()
        print("✓ test_negar_rejeicao_estado_draft passed")
        
        test_invalid_transitions.test_negar_rejeicao_estado_processing()
        print("✓ test_negar_rejeicao_estado_processing passed")
        
        test_invalid_transitions.test_negar_marcar_como_processado_estado_draft()
        print("✓ test_negar_marcar_como_processado_estado_draft passed")
    except Exception as e:
        print(f"✗ test_invalid_transitions failed: {e}")
        return False
    
    print("\nRunning test_permissions...")
    try:
        test_permissions.test_admin_pode_aprovar_relato()
        print("✓ test_admin_pode_aprovar_relato passed")
        
        test_permissions.test_colaborador_pode_aprovar_relato()
        print("✓ test_colaborador_pode_aprovar_relato passed")
        
        test_permissions.test_usuario_comum_nao_pode_aprovar_relato()
        print("✓ test_usuario_comum_nao_pode_aprovar_relato passed")
        
        test_permissions.test_admin_pode_rejeitar_relato()
        print("✓ test_admin_pode_rejeitar_relato passed")
        
        test_permissions.test_colaborador_pode_rejeitar_relato()
        print("✓ test_colaborador_pode_rejeitar_relato passed")
        
        test_permissions.test_usuario_comum_nao_pode_rejeitar_relato()
        print("✓ test_usuario_comum_nao_pode_rejeitar_relato passed")
        
        test_permissions.test_admin_pode_arquivar_relato()
        print("✓ test_admin_pode_arquivar_relato passed")
        
        test_permissions.test_colaborador_pode_arquivar_relato()
        print("✓ test_colaborador_pode_arquivar_relato passed")
        
        test_permissions.test_usuario_comum_nao_pode_arquivar_relato()
        print("✓ test_usuario_comum_nao_pode_arquivar_relato passed")
    except Exception as e:
        print(f"✗ test_permissions failed: {e}")
        return False
    
    print("\nAll tests passed!")
    return True

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n✅ All domain tests passed successfully!")
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
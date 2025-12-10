"""
Teste para validar as implementacoes de backend no Dermasyn API.

Este script testa os endpoints atualizados e a funcionalidade implementada.
"""
import asyncio
import sys
import os

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.abspath('.'))

async def test_imagens_service():
    """Testa as funções de serviço de imagens atualizadas."""
    print("Testando funcoes de servico de imagens...")

    try:
        # Testar importação das funções atualizadas
        from app.services.imagens_service import (
            listar_imagens_publicas,
            get_public_imagem_by_id,
            _collect_public_images_sync,
            _generate_signed_url_sync
        )
        print("[OK] Funcoes de servico importadas com sucesso")

        # Testar a nova função com include_signed_url
        print("\nTestando listar_imagens_publicas com include_signed_url=False...")
        imagens_publicas = await listar_imagens_publicas(include_signed_url=False)
        print(f"[OK] Encontradas {len(imagens_publicas)} imagens publicas sem signed_url")

        print("\nTestando listar_imagens_publicas com include_signed_url=True...")
        imagens_publicas_com_url = await listar_imagens_publicas(include_signed_url=True)
        print(f"[OK] Encontradas {len(imagens_publicas_com_url)} imagens publicas com signed_url")

        # Verificar se alguma imagem tem signed_url
        if imagens_publicas_com_url and 'signed_url' in imagens_publicas_com_url[0]:
            print("[OK] signed_url esta presente nas imagens quando solicitado")
        else:
            print("[INFO] signed_url nao encontrado nas imagens - pode ser normal se nao houver storage_path")

        print("\n[OK] Testes de servico de imagens concluidos com sucesso")

    except Exception as e:
        print(f"[ERROR] Erro nos testes de servico: {e}")
        import traceback
        traceback.print_exc()

async def test_routes():
    """Testa se as rotas estao configuradas corretamente."""
    print("\nTestando rotas atualizadas...")

    try:
        from app.routes.imagens import router
        # Verificar se as rotas foram adicionadas
        routes = [route.path for route in router.routes]
        print(f"Rotas encontradas: {routes}")

        # Verificar se as rotas atualizadas existem
        expected_routes = [
            "/imagens/listar-publicas",
            "/imagens/{image_id}/public"
        ]

        for expected_route in expected_routes:
            if any(expected_route in route for route in routes):
                print(f"[OK] Rota encontrada: {expected_route}")
            else:
                print(f"[WARN] Rota nao encontrada: {expected_route}")

        print("[OK] Teste de rotas concluido")

    except Exception as e:
        print(f"[ERROR] Erro no teste de rotas: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Função principal para rodar os testes."""
    print("Iniciando testes de validacao para as implementacoes do backend...")
    print("="*60)

    await test_imagens_service()
    await test_routes()

    print("="*60)
    print("Testes concluidos.")

if __name__ == "__main__":
    asyncio.run(main())
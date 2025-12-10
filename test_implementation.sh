#!/bin/bash
# Script de testes para validar as implementações realizadas

echo "Testando endpoints da API Dermasyn..."

# Teste 1: Listar imagens públicas sem signed_url
echo "Teste 1: GET /imagens/listar-publicas"
curl -X GET "http://localhost:8000/imagens/listar-publicas" -H "Content-Type: application/json"
echo -e "\n"

# Teste 2: Listar imagens públicas com signed_url
echo "Teste 2: GET /imagens/listar-publicas?include_signed_url=true"
curl -X GET "http://localhost:8000/imagens/listar-publicas?include_signed_url=true" -H "Content-Type: application/json"
echo -e "\n"

# Teste 3: Buscar imagem pública específica sem signed_url
echo "Teste 3: GET /imagens/{image_id}/public"
curl -X GET "http://localhost:8000/imagens/some-image-id/public" -H "Content-Type: application/json"
echo -e "\n"

# Teste 4: Buscar imagem pública específica com signed_url
echo "Teste 4: GET /imagens/{image_id}/public?include_signed_url=true"
curl -X GET "http://localhost:8000/imagens/some-image-id/public?include_signed_url=true" -H "Content-Type: application/json"
echo -e "\n"

echo "Testes completados. Verifique os logs do servidor para validar o middleware de logging."
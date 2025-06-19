# 📊 DermaSync - Test Report

## Objetivo

Garantir que a extração de dados semânticos a partir de relatos de pacientes gere objetos JSON em conformidade com o contrato definido, e que erros sejam detectados precocemente no pipeline.

---

## ✅ Testes Implementados

### `test_extracao_basica.py`

| Teste                          | Descrição                                                                 | Status     |
|-------------------------------|---------------------------------------------------------------------------|------------|
| `test_extracao_conforme_schema` | Testa se o JSON gerado a partir de um relato simples está conforme o schema mínimo. Também valida conteúdos esperados como gênero, idade e sintomas. | ✅ Implementado |

---

## 🧪 Cobertura Atual

- [x] Gênero (masculino/feminino)
- [x] Idade (inteiro)
- [x] Sintomas (lista de strings)
- [x] Tratamentos (lista de strings)

---

## ⚠️ Testes Pendentes

- [ ] Testes com relatos ambíguos ou vagos
- [ ] Testes com erros deliberados no input (testes de robustez)
- [ ] Teste com múltiplas ocorrências de idade ou tratamento
- [ ] Casos onde não há tratamento identificado
- [ ] Performance mínima com lote de 50 relatos

---

## 🔧 Como rodar os testes

```bash
pip install -r requirements.txt
pytest tests/

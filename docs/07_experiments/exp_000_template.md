# Experimento: Firestore local

**Data:** 2026-04-12
**Responsável:** Jefferson
**Status:** Em andamento

## 1. Hipótese
Firestore rodando locamente.

## 2. Metodologia (Setup)
criação do firestore.json local (versao inicial)

{
  "emulators": {
    "firestore": {
      "host": "127.0.0.1",
      "port": 8080
    }
  }
}

modificacao no client.py para nova mudança.

Ordem do teste:

subir emulador
firebase emulators:start --only firestore --project dermasync-local

rodar teste
python .\test_local_firestore.py

## 3. Resultados
| Métrica | Baseline | Variante A |
| :--- | :--- | :--- |
| Latência | | |
| Acurácia | | |

## 4. Conclusão e Próximos Passos
O que aprendemos? A hipótese se confirmou?

# debug_jwt.py
# -*- coding: utf-8 -*-
"""
Ferramenta simples de depuração local para tokens JWT.
Decodifica header, payload e converte timestamps.
Opcionalmente valida assinatura se JWT_SECRET estiver configurado no ambiente.
"""

import os
import json
import base64
from datetime import datetime
from jose import jwt, JWTError


def b64decode(segment: str) -> dict:
    """Decodifica Base64URL (sem verificar assinatura)."""
    padded = segment + "=" * (-len(segment) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
    return json.loads(decoded.decode("utf-8"))


def decode_jwt_no_verify(token: str):
    """Decodifica um JWT, mesmo que tenha sido colado com pontos extras (ex: truncado com '...')."""
    parts = token.split(".")

    if len(parts) < 3:
        raise ValueError("Token JWT inválido: precisa de pelo menos 3 segmentos.")

    # Garante que só os 3 primeiros são usados
    header_b64, payload_b64, signature_b64 = parts[:3]

    header = b64decode(header_b64)
    payload = b64decode(payload_b64)

    print("\n===== HEADER =====")
    print(json.dumps(header, indent=4, ensure_ascii=False))

    print("\n===== PAYLOAD =====")
    print(json.dumps(payload, indent=4, ensure_ascii=False))

    # converter timestamps
    for field in ("iat", "exp"):
        if field in payload:
            ts = payload[field]
            try:
                dt = datetime.utcfromtimestamp(ts)
                print(f"{field}: {dt} UTC")
            except Exception:
                pass

    print("\n===== SIGNATURE (raw) =====")
    print(signature_b64)
    print("\n")



def verify_signature(token: str):
    """Valida a assinatura usando JWT_SECRET (opcional)."""
    secret = os.getenv("JWT_SECRET")
    if not secret:
        print("⚠️  JWT_SECRET não definido no ambiente. Pulando verificação.")
        return

    print("Verificando assinatura...")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        print("✔ Assinatura válida.")
        print("Payload validado:\n", json.dumps(payload, indent=4, ensure_ascii=False))
    except JWTError as e:
        print("❌ Assinatura inválida ou token expirado:", e)


if __name__ == "__main__":
    print("Digite o token JWT:")
    token = input("> ").strip()

    print("\n\n============================")
    print(" DECODIFICAÇÃO DO TOKEN JWT ")
    print("============================")

    decode_jwt_no_verify(token)
    verify_signature(token)      

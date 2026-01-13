# app/services/retry_relato.py

from app.services.effects.fetch_firestore import fetch_failed_effects
from app.services.effects.retry_effect_executor import RetryEffectExecutor
from app.domain.effects.commands import EffectCommand
from app.services.contracts import ServiceResult
from app.domain.ux_effects.retry import RetryUXEffect


def retry_failed_effects(*, relato_id: str) -> ServiceResult:
    failed_results = fetch_failed_effects(relato_id=relato_id)

    # 🟢 Caso não haja nada para retry
    if not failed_results:
        return ServiceResult(
            ux_effects=[
                RetryUXEffect.none_needed(
                    relato_id=relato_id
                )
            ]
        )

    # 🔁 Converte EffectResults técnicos em comandos de domínio
    commands = [
        _effect_result_to_command(result)
        for result in failed_results
    ]

    executor = RetryEffectExecutor()
    executor.execute(commands)

    # 🔔 Emite efeito UX informando retry em andamento
    return ServiceResult(
        ux_effects=[
            RetryUXEffect.retrying(
                relato_id=relato_id,
                count=len(failed_results),
            )
        ]
    )


def _effect_result_to_command(effect_result) -> EffectCommand:
    return EffectCommand(
        type=effect_result.effect_type,
        relato_id=effect_result.relato_id,
        effect_ref=effect_result.effect_ref,
        metadata=effect_result.metadata,
    )

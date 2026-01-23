from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
#from .progress_aggregator import UXProgress, UXStep


# ============================================================
# Linguagem do domínio (Ubiquitous Language)
# ============================================================

class StepState(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"
    ERROR = "error"


# ============================================================
# Modelos semânticos
# ============================================================

@dataclass
class UXStep:
    step_id: str
    label: str
    weight: int
    state: StepState
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class UXProgress:
    relato_id: str
    steps: List[UXStep]
    progress_pct: float
    is_complete: bool
    has_error: bool
    summary: str
    updated_at: datetime


# ============================================================
# Contratos observáveis (vindos de fora do domínio UX)
# ============================================================

@dataclass
class EffectResult:
    type: str
    success: bool
    executed_at: datetime
    error_message: Optional[str] 
    metadata: Optional[Dict]


@dataclass
class UXStepDefinition:
    step_id: str
    label: str
    weight: int
    completion_effect_type: str


# ============================================================
# Domain Service — Agregador de Progresso
# ============================================================

def aggregate_progress(
    relato_id: str,
    step_definitions: List[UXStepDefinition],
    effect_results: List[EffectResult],
    now: Optional[datetime] = None,
) -> UXProgress:
    """
    Agregador puro de progresso UX.

    - Não executa efeitos
    - Não conhece infraestrutura
    - Deriva narrativa cognitiva a partir de evidências (EffectResult)
    """

    now = now or datetime.utcnow()

    # --------------------------------------------------------
    # Indexa effects por tipo para lookup eficiente
    # --------------------------------------------------------
    effects_by_type: dict[str, list[EffectResult]] = {}
    for effect in effect_results:
        effects_by_type.setdefault(effect.type, []).append(effect)

    steps: List[UXStep] = []

    # --------------------------------------------------------
    # Inferência semântica de cada UXStep
    # --------------------------------------------------------
    for definition in step_definitions:
        related_effects = effects_by_type.get(
            definition.completion_effect_type, []
        )

        # Caso 1 — Nenhuma evidência ainda
        if not related_effects:
            steps.append(
                UXStep(
                    step_id=definition.step_id,
                    label=definition.label,
                    weight=definition.weight,
                    state=StepState.PENDING,
                )
            )
            continue

        # Separa sucesso e erro
        success_effects = [e for e in related_effects if e.success]
        error_effects = [e for e in related_effects if not e.success]

        # Caso 2 — Sucesso observado (DONE)
        if success_effects:
            first_event = min(related_effects, key=lambda e: e.executed_at)
            last_success = max(success_effects, key=lambda e: e.executed_at)

            steps.append(
                UXStep(
                    step_id=definition.step_id,
                    label=definition.label,
                    weight=definition.weight,
                    state=StepState.DONE,
                    started_at=first_event.executed_at,
                    finished_at=last_success.executed_at,
                )
            )
            continue

        # Caso 3 — Houve tentativa, mas não sucesso (ACTIVE)
        first_event = min(related_effects, key=lambda e: e.executed_at)
        last_error = max(error_effects, key=lambda e: e.executed_at)

        steps.append(
            UXStep(
                step_id=definition.step_id,
                label=definition.label,
                weight=definition.weight,
                state=StepState.ACTIVE,
                started_at=first_event.executed_at,
                error_message=last_error.error_message,
            )
        )

    # --------------------------------------------------------
    # Derivações globais (invariantes do agregado)
    # --------------------------------------------------------
    total_weight = sum(step.weight for step in steps)
    done_weight = sum(
        step.weight for step in steps if step.state == StepState.DONE
    )

    progress_pct = done_weight / total_weight if total_weight > 0 else 0.0

    has_error = any(step.state == StepState.ERROR for step in steps)
    is_complete = all(step.state == StepState.DONE for step in steps)

    # --------------------------------------------------------
    # Summary — narrativa humana
    # --------------------------------------------------------
    if has_error:
        summary = next(
            step.label for step in steps if step.state == StepState.ERROR
        )
    else:
        done_steps = [s for s in steps if s.state == StepState.DONE]
        summary = done_steps[-1].label if done_steps else "Relato recebido"

    # --------------------------------------------------------
    # Retorno do agregado semântico
    # --------------------------------------------------------
    return UXProgress(
        relato_id=relato_id,
        steps=steps,
        progress_pct=progress_pct,
        is_complete=is_complete,
        has_error=has_error,
        summary=summary,
        updated_at=now,
    )

def find_step(progress: UXProgress, step_id: str) -> Optional[UXStep]:
    """
    Retorna o UXStep correspondente ao step_id informado.

    - Não lança exceção
    - Não infere nada
    - Expressa intenção semântica do domínio
    """

    for step in progress.steps:
        if step.step_id == step_id:
            return step

    return None

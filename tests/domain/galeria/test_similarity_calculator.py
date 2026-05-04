from app.domain.galeria.similarity.calculator import SimilarityCalculator
from app.domain.galeria.similarity.policy import SimilarityPolicy
from app.domain.galeria.similarity.axes import SimilarityAxis


def test_user_with_low_similarity_gets_summary():
    resolver = ExposureStageResolver()

    stage, can_request_more = resolver.resolve(
        eligibility=RelatoEligibilityDecision(
            eligible=True,
            reason="similarity_required",
            similarity_required=True,
            min_similarity=0.7,
        ),
        similarity=0.4,
        user=UserCognitiveProfile(...),
    )

    assert stage == ExposureStage.SUMMARY
    assert can_request_more is True


def test_similarity_policy_v1_weights_sum_to_one():
    from app.domain.galeria.similarity.policy import SIMILARITY_POLICY_V1

    total = sum(SIMILARITY_POLICY_V1.weights.values())
    assert round(total, 5) == 1.0


def test_jaccard_similarity_basic():
    from app.domain.galeria.similarity.scorers.tags_overlap import jaccard_similarity

    a = ["coceira", "vermelhidão"]
    b = ["coceira", "descamação"]

    assert jaccard_similarity(a, b) == round(1 / 3, 4)

def test_similarity_score_is_compositional_and_deterministic():
    calculator = SimilarityCalculator()

    policy = SimilarityPolicy(
        version="test",
        weights={
            SimilarityAxis.SYMPTOMS: 0.5,
            SimilarityAxis.BODY_REGION: 0.5,
        },
    )

    partial_scores = {
        SimilarityAxis.SYMPTOMS: 0.8,
        SimilarityAxis.BODY_REGION: 0.6,
    }

    result = calculator.calculate(
        partial_scores=partial_scores,
        policy=policy,
    )

    assert result.total == 0.7
    assert round(sum(result.breakdown.values()), 4) == 0.7
    
    

import pytest
from pydantic import ValidationError

from agent.verifier_schema import (
    ClaimAnalysis,
    SourceTierDistribution,
    VeritabilityReport,
)


def make_claim(**overrides):
    values = {
        "claim_text": "The event occurred in 2026.",
        "status": "VERIFIED",
        "confidence_score": 85,
        "reasoning": "Two independent sources support the date.",
        "citation_links": ["https://example.com/source"],
    }
    values.update(overrides)
    return ClaimAnalysis(**values)


def make_source_spectrum(**overrides):
    values = {
        "tier_1_count": 1,
        "tier_2_count": 2,
        "tier_3_count": 0,
        "spectrum_analysis": "Most evidence came from established sources.",
    }
    values.update(overrides)
    return SourceTierDistribution(**values)


@pytest.mark.parametrize("score", [-1, 101])
def test_claim_confidence_rejects_scores_outside_percentage_range(score):
    with pytest.raises(ValidationError):
        make_claim(confidence_score=score)


def test_claim_status_rejects_unknown_value():
    with pytest.raises(ValidationError):
        make_claim(status="MAYBE")


def test_source_counts_cannot_be_negative():
    with pytest.raises(ValidationError):
        make_source_spectrum(tier_1_count=-1)


@pytest.mark.parametrize("score", [-1, 101])
def test_report_rejects_truth_scores_outside_percentage_range(score):
    with pytest.raises(ValidationError):
        VeritabilityReport(
            headline_under_test="Example headline",
            overall_truth_score=score,
            verdict_summary="Example summary",
            atomic_claims=[make_claim()],
            key_sources=["Example source"],
            source_spectrum=make_source_spectrum(),
        )


def test_report_accepts_boundary_scores():
    for score in (0, 100):
        report = VeritabilityReport(
            headline_under_test="Example headline",
            overall_truth_score=score,
            verdict_summary="Example summary",
            atomic_claims=[make_claim(confidence_score=score)],
            key_sources=["Example source"],
            source_spectrum=make_source_spectrum(),
        )

        assert report.overall_truth_score == score

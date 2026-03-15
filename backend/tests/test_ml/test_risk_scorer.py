"""Tests for the risk scorer aggregation logic."""

import pytest

from app.ml.risk_scorer import RiskScorer
from app.models.analysis import DetectionResult


@pytest.fixture
def scorer():
    return RiskScorer()


def _make_result(score: float, confidence: float = 0.8) -> DetectionResult:
    return DetectionResult(score=score, confidence=confidence, evidence={})


def test_all_zero_scores(scorer):
    """All detectors reporting zero should give a safe result."""
    results = {
        "typosquatting": _make_result(0),
        "code_analysis": _make_result(0),
        "behavior": _make_result(0),
        "maintainer": _make_result(0),
        "dependency": _make_result(0),
    }
    analysis = scorer.calculate_risk(results)
    assert analysis.risk_score == 0.0
    assert analysis.threat_level == "safe"
    assert analysis.is_malicious is False


def test_critical_scores(scorer):
    """High scores across the board should produce a critical result."""
    results = {
        "typosquatting": _make_result(95),
        "code_analysis": _make_result(90),
        "behavior": _make_result(80),
        "maintainer": _make_result(85),
        "dependency": _make_result(70),
    }
    analysis = scorer.calculate_risk(results)
    assert analysis.risk_score > 80
    assert analysis.threat_level == "critical"
    assert analysis.is_malicious is True


def test_mixed_scores(scorer):
    """A mix of high and low scores should land in the middle."""
    results = {
        "typosquatting": _make_result(90),
        "code_analysis": _make_result(10),
        "behavior": _make_result(5),
        "maintainer": _make_result(0),
        "dependency": _make_result(0),
    }
    analysis = scorer.calculate_risk(results)
    assert 15 < analysis.risk_score < 40


def test_confidence_full_agreement(scorer):
    """All detectors above threshold should yield high confidence."""
    results = {
        "typosquatting": _make_result(80),
        "code_analysis": _make_result(70),
        "behavior": _make_result(60),
        "maintainer": _make_result(55),
        "dependency": _make_result(65),
    }
    analysis = scorer.calculate_risk(results)
    assert analysis.confidence == 1.0


def test_missing_detector_treated_as_zero(scorer):
    """If a detector is None, it should contribute 0."""
    results = {
        "typosquatting": _make_result(90),
        "code_analysis": None,
        "behavior": None,
        "maintainer": None,
        "dependency": None,
    }
    analysis = scorer.calculate_risk(results)
    # Only typosquatting contributes: 90 * 0.25 = 22.5
    assert abs(analysis.risk_score - 22.5) < 0.5

"""Stage 6 verification: metric math and the end-to-end evaluation report."""

from app.eval.harness import run_evaluation
from app.eval.metrics import prf


def test_prf_math() -> None:
    result = prf(true_positives=8, false_positives=2, false_negatives=0)
    assert result.precision == 0.8
    assert result.recall == 1.0
    assert round(result.f1, 4) == 0.8889


def test_prf_handles_empty_gracefully() -> None:
    result = prf(0, 0, 0)
    assert result.precision == 0.0
    assert result.recall == 0.0
    assert result.f1 == 0.0


def test_evaluation_report_hits_targets(tmp_path) -> None:
    report = run_evaluation(seed=42, workdir=tmp_path)

    # PII: recall must be perfect on the golden set (proven in Stage 3).
    assert report.pii.name_detection.recall >= 0.95
    assert report.pii.persons_found == report.pii.persons_expected

    # Guardrails: high catch, zero false positives (proven in Stage 5).
    assert report.guardrails.catch_rate >= 0.9
    assert report.guardrails.false_positive_rate == 0.0

    # Safety: no original PII leaked into pseudonymized output.
    assert report.safety.zero_leak
    assert report.safety.leaked_tokens == []
    assert report.safety.replaced_cells > 0

    # Report is JSON-serializable for the dashboard.
    assert isinstance(report.to_dict(), dict)
    assert report.duration_seconds > 0


def test_report_is_stable_across_runs(tmp_path) -> None:
    a = run_evaluation(seed=42, workdir=tmp_path / "a")
    b = run_evaluation(seed=42, workdir=tmp_path / "b")
    assert a.pii.name_detection.recall == b.pii.name_detection.recall
    assert a.guardrails.catch_rate == b.guardrails.catch_rate


def test_refactor_eval_verifier_is_correct(tmp_path) -> None:
    report = run_evaluation(seed=42, workdir=tmp_path)
    # The fidelity verifier must score a faithful copy 1.0 and catch both
    # a missing field and an extra one.
    assert report.refactor.verifier_correct
    assert report.refactor.perfect_score == 1.0
    assert report.refactor.missing_detected
    assert report.refactor.extra_detected

"""Stage 9 verification: spec comparison math and the self-check loop.

All offline: the LLM steps are scripted via FakeProvider, so the loop's
control flow (generate -> verify -> refine) is tested deterministically.
"""

import json

from app.llm.client import LLMClient
from app.llm.providers import FakeProvider
from app.refactor.schemas import UIField, UISpec
from app.refactor.service import RefactorService, compare_specs


def _spec(*fields: tuple[str, str]) -> UISpec:
    return UISpec(
        title="Customer Form",
        fields=[
            UIField(type=t, label=lbl, name=lbl.lower().replace(" ", "_"))
            for t, lbl in fields
        ],
    )


# ── Structural comparison (pure, no LLM) ─────────────────────────────

def test_identical_specs_score_one() -> None:
    spec = _spec(("input", "Customer Name"), ("input", "City"), ("button", "Save"))
    report = compare_specs(spec, spec)
    assert report.score == 1.0
    assert report.missing == []


def test_missing_field_lowers_score() -> None:
    target = _spec(("input", "Customer Name"), ("input", "City"), ("button", "Save"))
    produced = _spec(("input", "Customer Name"), ("button", "Save"))
    report = compare_specs(target, produced)
    assert report.score < 1.0
    assert "city" in report.missing


def test_label_fuzzy_match_tolerates_wording() -> None:
    target = _spec(("input", "Customer Name"))
    produced = _spec(("input", "Customer name *"))  # trailing marker, different case
    report = compare_specs(target, produced)
    assert report.score == 1.0


def test_type_mismatch_is_not_a_match() -> None:
    target = _spec(("select", "Country"))
    produced = _spec(("input", "Country"))
    report = compare_specs(target, produced)
    assert report.score == 0.0
    assert "country" in report.missing


# ── Self-check loop (scripted LLM) ───────────────────────────────────

TARGET_SPEC = _spec(("input", "Customer Name"), ("input", "City"), ("button", "Save"))


def _component(*labels: str) -> str:
    # Minimal fake "code" — recovery step is also scripted, so contents are free.
    return json.dumps(
        {"framework": "angular", "filename": "customer-form.component.ts",
         "code": "// " + ", ".join(labels), "notes": ""}
    )


def _recovered(*fields: tuple[str, str]) -> str:
    spec = _spec(*fields)
    return spec.model_dump_json()


def test_loop_stops_when_fidelity_met_first_try() -> None:
    provider = FakeProvider(responses=[
        TARGET_SPEC.model_dump_json(),                                   # extract
        _component("Customer Name", "City", "Save"),                     # generate #1
        _recovered(("input", "Customer Name"), ("input", "City"), ("button", "Save")),  # recover #1
    ])
    service = RefactorService(llm=LLMClient(provider=provider))

    result = service.refactor("fake_base64", threshold=0.9)

    assert result.fidelity.score == 1.0
    assert result.fidelity.iterations == 1


def test_loop_refines_when_first_attempt_incomplete() -> None:
    provider = FakeProvider(responses=[
        TARGET_SPEC.model_dump_json(),                                   # extract
        _component("Customer Name", "Save"),                    # generate #1 (missing City)
        _recovered(("input", "Customer Name"), ("button", "Save")),      # recover #1 -> 0.67
        _component("Customer Name", "City", "Save"),                     # generate #2 (fixed)
        _recovered(("input", "Customer Name"), ("input", "City"), ("button", "Save")),  # recover #2
    ])
    service = RefactorService(llm=LLMClient(provider=provider))

    result = service.refactor("fake_base64", threshold=0.9, max_iterations=3)

    assert result.fidelity.iterations == 2
    assert result.fidelity.score == 1.0
    # The refine step must have fed the missing field back to the generator.
    generate_calls = [c for c in provider.calls if "Missing fields" in c["prompt"]]
    assert any("city" in c["prompt"].lower() for c in generate_calls)


def test_extract_spec_passes_image_to_provider() -> None:
    provider = FakeProvider(responses=[TARGET_SPEC.model_dump_json()])
    service = RefactorService(llm=LLMClient(provider=provider))

    service.extract_spec("base64imagedata")

    assert provider.calls[0]["has_image"] is True
